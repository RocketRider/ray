import unittest

import numpy as np

import ray
import ray.rllib.algorithms.ppo as ppo
from ray.rllib.algorithms.ppo.ppo_learner import (
    LEARNER_RESULTS_CURR_ENTROPY_COEFF_KEY,
)
from ray.rllib.algorithms.callbacks import DefaultCallbacks
from ray.rllib.algorithms.ppo.tests.test_ppo import PENDULUM_FAKE_BATCH
from ray.rllib.core.learner.learner import (
    LEARNER_RESULTS_CURR_LR_KEY,
)
from ray.rllib.evaluation.postprocessing import (
    compute_gae_for_sample_batch,
)
from ray.rllib.policy.sample_batch import DEFAULT_POLICY_ID
from ray.rllib.utils.metrics.learner_info import LEARNER_INFO
from ray.rllib.utils.test_utils import (
    check,
    check_compute_single_action,
    check_train_results,
    framework_iterator,
)


def get_model_config(framework, lstm=False):
    model_config = {
        "torch": dict(
            # Settings in case we use an LSTM.
            lstm_cell_size=10,
            max_seq_len=20,
        ),
        "tf2": dict(
            fcnet_activation="relu",
            fcnet_hiddens=[32, 32],
            vf_share_layers=False,
        ),
    }
    if framework == "tf2":
        return model_config["tf2"]
    elif framework == "torch":
        torch_model_config = model_config["torch"]
        for k in [
            "use_lstm",
            "lstm_use_prev_action",
            "lstm_use_prev_reward",
            "vf_share_layers",
        ]:
            torch_model_config[k] = lstm
        return model_config["torch"]


class MyCallbacks(DefaultCallbacks):
    def on_train_result(self, *, algorithm, result: dict, **kwargs):
        stats = result["info"][LEARNER_INFO][DEFAULT_POLICY_ID]
        # Entropy coeff goes to 0.05, then 0.0 (per iter).
        check(
            stats[LEARNER_RESULTS_CURR_ENTROPY_COEFF_KEY],
            0.05 if algorithm.iteration == 1 else 0.0,
        )

        # Learning rate should decrease by 0.0001 per iteration.
        check(
            stats[LEARNER_RESULTS_CURR_LR_KEY],
            0.0003 if algorithm.iteration == 1 else 0.0002,
        )
        # Compare reported curr lr vs the actual lr found in the optimizer object.
        optim = algorithm.learner_group._learner._named_optimizers[DEFAULT_POLICY_ID]
        actual_optimizer_lr = (
            optim.param_groups[0]["lr"]
            if algorithm.config.framework_str == "torch"
            else optim.lr
        )
        check(stats[LEARNER_RESULTS_CURR_LR_KEY], actual_optimizer_lr)


class TestPPO(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ray.init()

    @classmethod
    def tearDownClass(cls):
        ray.shutdown()

    def test_ppo_compilation_and_schedule_mixins(self):
        """Test whether PPO can be built with all frameworks."""

        # Build a PPOConfig object.
        config = (
            ppo.PPOConfig()
            .training(
                num_sgd_iter=2,
                # Setup lr schedule for testing lr-scheduling correctness.
                lr_schedule=[[0, 0.0004], [512, 0.0]],  # 512=4x128
                # Set entropy_coeff to a faulty value to proof that it'll get
                # overridden by the schedule below (which is expected).
                entropy_coeff=100.0,
                entropy_coeff_schedule=[[0, 0.1], [256, 0.0]],  # 256=2x128
                train_batch_size=128,
                _enable_learner_api=True,
            )
            .rollouts(
                num_rollout_workers=1,
                # Test with compression.
                # compress_observations=True,
                enable_connectors=True,
            )
            .callbacks(MyCallbacks)
            .rl_module(_enable_rl_module_api=True)
        )

        num_iterations = 2

        for fw in framework_iterator(
            config, frameworks=("torch", "tf2"), with_eager_tracing=True
        ):
            # TODO (Kourosh) Bring back "FrozenLake-v1"
            for env in ["CartPole-v1", "Pendulum-v1", "ALE/Breakout-v5"]:
                print("Env={}".format(env))
                # TODO (Kourosh, Avnishn): for now just do lstm=False
                for lstm in [False]:
                    print("LSTM={}".format(lstm))
                    config.training(model=get_model_config(fw, lstm=lstm))

                    algo = config.build(env=env)
                    optim = algo.learner_group._learner._named_optimizers[
                        DEFAULT_POLICY_ID
                    ]
                    entropy_coeff = algo.get_policy().entropy_coeff
                    lr = optim.param_groups[0]["lr"] if fw == "torch" else optim.lr
                    check(entropy_coeff, 0.1)
                    # Check initial LR directly set in optimizer.
                    check(lr, config.lr)

                    for i in range(num_iterations):
                        results = algo.train()
                        check_train_results(results)
                        print(results)

                    check_compute_single_action(
                        algo, include_prev_action_reward=True, include_state=lstm
                    )
                    algo.stop()

    def test_ppo_exploration_setup(self):
        """Tests, whether PPO runs with different exploration setups."""
        config = (
            ppo.PPOConfig()
            .environment(
                "FrozenLake-v1",
                env_config={"is_slippery": False, "map_name": "4x4"},
            )
            .rollouts(
                # Run locally.
                num_rollout_workers=1,
                enable_connectors=True,
            )
            .rl_module(_enable_rl_module_api=True)
        )
        obs = np.array(0)

        for _ in framework_iterator(
            config, frameworks=("torch", "tf2"), with_eager_tracing=True
        ):
            # Default Agent should be setup with StochasticSampling.
            trainer = config.build()
            # explore=False, always expect the same (deterministic) action.
            a_ = trainer.compute_single_action(
                obs, explore=False, prev_action=np.array(2), prev_reward=np.array(1.0)
            )

            for _ in range(50):
                a = trainer.compute_single_action(
                    obs,
                    explore=False,
                    prev_action=np.array(2),
                    prev_reward=np.array(1.0),
                )
                check(a, a_)

            # With explore=True (default), expect stochastic actions.
            actions = []
            for _ in range(300):
                actions.append(
                    trainer.compute_single_action(
                        obs, prev_action=np.array(2), prev_reward=np.array(1.0)
                    )
                )
            check(np.mean(actions), 1.5, atol=0.2)
            trainer.stop()

    def test_ppo_free_log_std_with_rl_modules(self):
        """Tests the free log std option works."""
        config = (
            (
                ppo.PPOConfig()
                .environment("Pendulum-v1")
                .rollouts(
                    num_rollout_workers=0,
                )
                .training(
                    gamma=0.99,
                    model=dict(
                        fcnet_hiddens=[10],
                        fcnet_activation="linear",
                        free_log_std=True,
                        vf_share_layers=True,
                    ),
                )
            )
            .rl_module(_enable_rl_module_api=True)
            .training(_enable_learner_api=True)
        )

        for fw in framework_iterator(config, frameworks=("torch", "tf2")):
            trainer = config.build()
            policy = trainer.get_policy()

            # Check the free log std var is created.
            if fw == "torch":
                matching = [
                    v for (n, v) in policy.model.named_parameters() if "log_std" in n
                ]
            else:
                matching = [
                    v for v in policy.model.trainable_variables if "log_std" in str(v)
                ]
            assert len(matching) == 1, matching
            log_std_var = matching[0]

            # linter yells at you if you don't pass in the parameters.
            # reason: https://docs.python-guide.org/writing/gotchas/
            # #late-binding-closures
            def get_value(fw=fw, policy=policy, log_std_var=log_std_var):
                if fw == "torch":
                    return log_std_var.detach().cpu().numpy()[0]
                else:
                    return log_std_var.numpy()[0]

            # Check the variable is initially zero.
            init_std = get_value()
            assert init_std == 0.0, init_std
            batch = compute_gae_for_sample_batch(policy, PENDULUM_FAKE_BATCH.copy())
            if fw == "torch":
                batch = policy._lazy_tensor_dict(batch)
            policy.learn_on_batch(batch)

            # Check the variable is updated.
            post_std = get_value()
            assert post_std != 0.0, post_std
            trainer.stop()


if __name__ == "__main__":
    import pytest
    import sys

    sys.exit(pytest.main(["-v", __file__]))
