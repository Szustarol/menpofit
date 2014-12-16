import numpy as np
from scipy.linalg import norm

from .base import AppearanceLucasKanade


class PIC(AppearanceLucasKanade):
    r"""
    Project-Out Inverse Compositional algorithm
    """
    @property
    def algorithm(self):
        return 'ProjectOut-IC'

    def _set_up(self):
        # Compute warp Jacobian
        dW_dp = self.transform.d_dp(self.template.mask.true_indices())

        # Compute steepest descent images, VT_dW_dp
        J = self.residual.steepest_descent_images(
            self.template, dW_dp)

        # Project out appearance model from VT_dW_dp
        self._J = self.appearance_model.project_out_vectors(J.T).T

        # Compute Hessian and inverse
        self._H = self.residual.calculate_hessian(self._J)

    def _fit(self, fitting_result, max_iters=20):
        # Initial error > eps
        error = self.eps + 1
        image = fitting_result.image
        n_iters = 0

        # Baker-Matthews, Inverse Compositional Algorithm
        while n_iters < max_iters and error > self.eps:
            # Compute warped image with current weights
            IWxp = image.warp_to_mask(self.template.mask, self.transform,
                                      warp_landmarks=False)

            # Compute steepest descent parameter updates
            sd_delta_p = self.residual.steepest_descent_update(
                self._J, IWxp, self.template)

            # Compute gradient descent parameter updates
            delta_p = np.real(self._calculate_delta_p(sd_delta_p))

            # Request the pesudoinverse vector from the transform
            inv_delta_p = self.transform.pseudoinverse_vector(delta_p)

            # Update warp weights
            self.transform.compose_after_from_vector_inplace(inv_delta_p)
            fitting_result.parameters.append(self.transform.as_vector())

            # Test convergence
            error = np.abs(norm(delta_p))
            n_iters += 1

        return fitting_result
