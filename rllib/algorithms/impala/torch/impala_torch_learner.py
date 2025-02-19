from typing import Any, Dict, Mapping

from ray.rllib.algorithms.impala.impala_learner import ImpalaLearner
from ray.rllib.algorithms.impala.torch.vtrace_torch_v2 import (
    vtrace_torch,
    make_time_major,
)
from ray.rllib.algorithms.ppo.ppo_learner import LEARNER_RESULTS_CURR_ENTROPY_COEFF_KEY
from ray.rllib.core.learner.learner import ENTROPY_KEY
from ray.rllib.core.learner.torch.torch_learner import TorchLearner
from ray.rllib.core.rl_module.rl_module import ModuleID
from ray.rllib.policy.sample_batch import SampleBatch
from ray.rllib.utils.annotations import override
from ray.rllib.utils.framework import try_import_torch
from ray.rllib.utils.torch_utils import convert_to_torch_tensor
from ray.rllib.utils.typing import TensorType

torch, nn = try_import_torch()


class ImpalaTorchLearner(ImpalaLearner, TorchLearner):
    """Implements the IMPALA loss function in torch."""

    @override(TorchLearner)
    def compute_loss_per_module(
        self, module_id: str, batch: SampleBatch, fwd_out: Mapping[str, TensorType]
    ) -> TensorType:
        target_policy_dist = fwd_out[SampleBatch.ACTION_DIST]
        values = fwd_out[SampleBatch.VF_PREDS]

        behaviour_actions_logp = batch[SampleBatch.ACTION_LOGP]
        target_actions_logp = target_policy_dist.logp(batch[SampleBatch.ACTIONS])

        # TODO(Artur): In the old impala code, actions were unsqueezed if they were
        #  multi_discrete. Find out why and if we need to do the same here.
        #  actions = actions if is_multidiscrete else torch.unsqueeze(actions, dim=1)

        target_actions_logp_time_major = make_time_major(
            target_actions_logp,
            trajectory_len=self.hps.rollout_frag_or_episode_len,
            recurrent_seq_len=self.hps.recurrent_seq_len,
        )
        behaviour_actions_logp_time_major = make_time_major(
            behaviour_actions_logp,
            trajectory_len=self.hps.rollout_frag_or_episode_len,
            recurrent_seq_len=self.hps.recurrent_seq_len,
        )
        values_time_major = make_time_major(
            values,
            trajectory_len=self.hps.rollout_frag_or_episode_len,
            recurrent_seq_len=self.hps.recurrent_seq_len,
        )
        bootstrap_value = values_time_major[-1]
        rewards_time_major = make_time_major(
            batch[SampleBatch.REWARDS],
            trajectory_len=self.hps.rollout_frag_or_episode_len,
            recurrent_seq_len=self.hps.recurrent_seq_len,
        )

        # the discount factor that is used should be gamma except for timesteps where
        # the episode is terminated. In that case, the discount factor should be 0.
        discounts_time_major = (
            1.0
            - make_time_major(
                batch[SampleBatch.TERMINATEDS],
                trajectory_len=self.hps.rollout_frag_or_episode_len,
                recurrent_seq_len=self.hps.recurrent_seq_len,
            ).type(dtype=torch.float32)
        ) * self.hps.discount_factor

        # TODO(Artur) Why was there `TorchCategorical if is_multidiscrete else
        #  dist_class` in the old code torch impala policy?
        device = behaviour_actions_logp_time_major[0].device

        # Note that vtrace will compute the main loop on the CPU for better performance.
        vtrace_adjusted_target_values, pg_advantages = vtrace_torch(
            target_action_log_probs=target_actions_logp_time_major,
            behaviour_action_log_probs=behaviour_actions_logp_time_major,
            discounts=discounts_time_major,
            rewards=rewards_time_major,
            values=values_time_major,
            bootstrap_value=bootstrap_value,
            clip_rho_threshold=self.hps.vtrace_clip_rho_threshold,
            clip_pg_rho_threshold=self.hps.vtrace_clip_pg_rho_threshold,
        )

        # Sample size is T x B, where T is the trajectory length and B is the batch size
        # We mean over the batch size for consistency with the pre-RLModule
        # implementation of IMPALA
        # TODO(Artur): Mean over trajectory length after migration to RLModules.
        batch_size = (
            convert_to_torch_tensor(target_actions_logp_time_major.shape[-1])
            .float()
            .to(device)
        )

        # The policy gradients loss.
        pi_loss = -torch.sum(target_actions_logp_time_major * pg_advantages)
        mean_pi_loss = pi_loss / batch_size

        # The baseline loss.
        delta = values_time_major - vtrace_adjusted_target_values
        vf_loss = 0.5 * torch.sum(torch.pow(delta, 2.0))
        mean_vf_loss = vf_loss / batch_size

        # The entropy loss.
        mean_entropy_loss = -torch.mean(target_policy_dist.entropy())

        # The summed weighted loss.
        total_loss = (
            pi_loss
            + vf_loss * self.hps.vf_loss_coeff
            + mean_entropy_loss * self.hps.entropy_coeff
        )
        return {
            self.TOTAL_LOSS_KEY: total_loss,
            "pi_loss": mean_pi_loss,
            "vf_loss": mean_vf_loss,
            ENTROPY_KEY: -mean_entropy_loss,
        }

    @override(ImpalaLearner)
    def additional_update_per_module(
        self, module_id: ModuleID, timestep: int
    ) -> Dict[str, Any]:
        results = super().additional_update_per_module(
            module_id,
            timestep=timestep,
        )

        # Update entropy coefficient.
        value = self.hps.entropy_coeff
        if self.hps.entropy_coeff_schedule is not None:
            value = self.entropy_coeff_schedule_per_module[module_id].value(t=timestep)
            self.curr_entropy_coeffs_per_module[module_id].data = torch.tensor(value)
        results.update({LEARNER_RESULTS_CURR_ENTROPY_COEFF_KEY: value})

        return results
