#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fit distribution to data.
"""

from multiprocessing import Pool
import numpy as np
import statsmodels.api as sm
import scipy.stats as sts
from scipy.optimize import curve_fit
from compute.params import ConstantParam, FunctionParam
from compute.distributions import (WeibullDistribution, LognormalDistribution, NormalDistribution,
                                   KernelDensityDistribution,
                                   MultivariateDistribution)
import warnings

__all__ = ["Fit"]


# ----------------------------
# functions for fitting

def _f2(x, a, b, c):
    return a + b * np.exp(c * x)


def _f1(x, a, b, c):
    return a + b * x ** c

# ----------------------------


class Fit():
    """
    Holds data and information about a fit.

    Note
    ----
    The fitted results are not checked for correctness. The created distributions may not contain useful
    parameters. Distribution parameters are being checked in the contour creation process.

    Attributes
    ----------
    mul_var_dist : MultivariateDistribution,
        Distribution that is calculated

    mul_param_points : list,
        Length of dimensions, contains list with length of 3 (except for no dependency -> contains None) in the order
        (shape, loc, scale), each parameters contains list with length of 2 containing values of dependent dimension and
        the particular value of parameter

    mul_dist_points : list,
        Length of dimensions, contains list with length of 3 in the order (shape, loc, scale), each paramter contains
        list of samples used for fitting the particular parameter (i.e. length = 15 -> n_steps = 15, length = 1 -> no
        dependency)

    Examples
    --------
    Create a Fit and visualize the result in a IForm contour:

    >>> from multiprocessing import Pool
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> import statsmodels.api as sm
    >>> import scipy.stats as sts
    >>> from scipy.optimize import curve_fit
    >>> from compute.params import ConstantParam, FunctionParam
    >>> from compute.distributions import (WeibullDistribution,\
                                           LognormalDistribution,\
                                           NormalDistribution,\
                                           KernelDensityDistribution,\
                                           MultivariateDistribution)
    >>> from compute.contours import IFormContour
    >>> prng = np.random.RandomState(42)
    >>> sample_1 = prng.normal(10, 1, 500)
    >>> sample_2 = [point + prng.uniform(-5, 5) for point in sample_1]
    >>> dist_description_1 = {'name': 'KernelDensity', 'dependency': (None, None, None)}
    >>> dist_description_2 = {'name': 'Normal', 'dependency': (None, 0, None), 'functions':(None, 'f1', None)}
    >>> my_fit = Fit((sample_1, sample_2), (dist_description_1, dist_description_2), 5)
    >>> my_contour = IFormContour(my_fit.mul_var_dist)
    >>> #example_plot = plt.scatter(my_contour.coordinates[0][0], my_contour.coordinates[0][1], label="IForm")


    Create a Fit and visualize the result in a HDC contour:

    >>> from compute.contours import HighestDensityContour
    >>> sample_1 = prng.weibull(2, 500) + 15
    >>> sample_2 = [point + prng.uniform(-1, 1) for point in sample_1]
    >>> dist_description_1 = {'name': 'Weibull', 'dependency': (None, None, None)}
    >>> dist_description_2 = {'name': 'Normal', 'dependency': (None, None, None)}
    >>> my_fit = Fit((sample_1, sample_2), (dist_description_1, dist_description_2), 5)
    >>> return_period = 50
    >>> state_duration = 3
    >>> limits = [(0, 20), (0, 20)]
    >>> deltas = [0.05, 0.05]
    >>> my_contour = HighestDensityContour(my_fit.mul_var_dist, return_period, state_duration, limits, deltas,)
    >>> #example_plot2 = plt.scatter(my_contour.coordinates[0][0], my_contour.coordinates[0][1], label="HDC")


    An Example how to use the attributes mul_param_points and mul_dist_points to visualize how good your fit is:

    >>> dist_description_0 = {'name': 'Weibull', 'dependency': (None, None, None)}
    >>> dist_description_1 = {'name': 'Lognormal_1', 'dependency': (None, None, 0), 'functions': (None, None, 'f2')}
    >>> my_fit = Fit((sample_1, sample_2), (dist_description_0, dist_description_1), 3)
    >>>
    >>> #fig = plt.figure(figsize=(10, 8))
    >>> #example_text = fig.suptitle("Dependence of 'scale'")
    >>>
    >>> #ax_1 = fig.add_subplot(221)
    >>> #title1 = ax_1.set_title("Fitted curve")
    >>> param_grid = my_fit.mul_param_points[1][2][0]
    >>> x_1 = np.linspace(5, 15, 100)
    >>> #ax1_plot = ax_1.plot(param_grid, my_fit.mul_param_points[1][2][1], 'x')
    >>> #example_plot1 = ax_1.plot(x_1, my_fit.mul_var_dist.distributions[1].scale(x_1))
    >>>
    >>> #ax_2 = fig.add_subplot(222)
    >>> #title2 = ax_2.set_title("Distribution '1'")
    >>> #ax2_hist = ax_2.hist(my_fit.mul_dist_points[1][2][0], normed=1)
    >>> shape = my_fit.mul_var_dist.distributions[1].shape(None)
    >>> scale = my_fit.mul_var_dist.distributions[1].scale(param_grid[0])
    >>> #ax2_plot = ax_2.plot(np.linspace(0, 20, 100), sts.lognorm.pdf(np.linspace(0, 20, 100), s=shape, scale=scale))
    >>>
    >>> #ax_3 = fig.add_subplot(223)
    >>> #title3 = ax_3.set_title("Distribution '2'")
    >>> #ax3_hist = ax_3.hist(my_fit.mul_dist_points[1][2][1], normed=1)
    >>> shape = my_fit.mul_var_dist.distributions[1].shape(None)
    >>> scale = my_fit.mul_var_dist.distributions[1].scale(param_grid[1])
    >>> #ax3_plot = ax_3.plot(np.linspace(0, 20, 100), sts.lognorm.pdf(np.linspace(0, 20, 100), s=shape, scale=scale))
    >>>
    >>> #ax_4 = fig.add_subplot(224)
    >>> #title4 = ax_4.set_title("Distribution '3'")
    >>> #ax4_hist = ax_4.hist(my_fit.mul_dist_points[1][2][2], normed=1)
    >>> shape = my_fit.mul_var_dist.distributions[1].shape(None)
    >>> scale = my_fit.mul_var_dist.distributions[1].scale(param_grid[2])
    >>> #ax4_plot = ax_4.plot(np.linspace(0, 20, 100), sts.lognorm.pdf(np.linspace(0, 20, 100), s=shape, scale=scale))

    """

    def __init__(self, samples, dist_descriptions, n_steps):
        """
        Creates a Fit, by computing the distribution that describes the samples 'best'.

        Parameters
        ----------
        samples : list,
            List that contains data to be fitted : samples[0] -> first variable (i.e. wave height)
                                                   samples[1] -> second variable
                                                   ...
        dist_descriptions : list,
            contains dictionary for each parameter. See note for further information.
        n_steps : int
            number of distributions used to fit shape, loc, scale

        Note
        ----
        dist_descriptions contains the following keys:

        name : str,
            name of distribution:

            - Weibull
            - Lognormal_1 (shape, scale)
            - Lognormal_2 (sigma, mu),
            - Normal
            - KernelDensity (no dependency)

        dependency : list,
            Length of 3 in the order (shape, loc, scale) contains:

            - None -> no dependency
            - int -> depends on particular dimension

        functions : list,
            Length of 3 in the order : (shape, loc, scale), usable options:

            - :f1: :math:`a + b * x^c`
            - :f2: :math:`a + b * e^{x * c}`
            - remark : in case of Lognormal_2 it is (sigma, loc=0, mu)
        """

        # multiprocessing for more performance
        pool = Pool()
        multiple_results = []

        # distribute work on cores
        for dimension in range(len(samples)):
            dist_description = dist_descriptions[dimension]

            dist_description['n_steps'] = n_steps
            multiple_results.append(
                pool.apply_async(self._get_distribution, (dimension, samples), dist_description))

        # initialize parameters for multivariate distribution
        distributions = []
        dependencies = []

        # initialize points for plotting the fits
        self.mul_param_points = []
        self.mul_dist_points = []

        # get distributions
        for res in multiple_results:
            distribution, dependency, dist_points, param_points = res.get(timeout=1e6)

            # saves distribution and dependency for particular dimension
            distributions.append(distribution)
            dependencies.append(dependency)

            # save fitting points for particular dimension
            self.mul_dist_points.append(dist_points)
            self.mul_param_points.append(param_points)

        # save multivariate distribution
        self.mul_var_dist = MultivariateDistribution(distributions, dependencies)

    @staticmethod
    def _fit_distribution(sample, name):
        """
        Fits the distribution and returns the parameters.

        Parameters
        ----------
        sample : list,
            raw data

        name : str,
            name of distribution (Weibull, Lognormal, Normal, KernelDensity (no dependency))

        """

        if name == 'Weibull':
            params = sts.weibull_min.fit(sample)
        elif name == 'Normal':
            params = list(sts.norm.fit(sample))
            # shape doesn't exist for normal
            params.insert(0, 0)
        elif name[:-2] == 'Lognormal':
            # For lognormal loc is set to 0
            params = sts.lognorm.fit(sample, floc=0)
        elif name == 'KernelDensity':
            dens = sm.nonparametric.KDEUnivariate(sample)
            dens.fit(gridsize=2000)
            # kernel density doesn't have shape, loc, scale
            return (dens.cdf, dens.icdf)
        return (ConstantParam(params[0]), ConstantParam(params[1]), ConstantParam(params[2]))

    @staticmethod
    def _get_function(function_name):
        """
        Returns the function.

        Parameters
        ----------
        function_name : str,
            options are 'f1', 'f2'
        """
        
        if function_name == 'f1':
            return _f1
        elif function_name == 'f2':
            return _f2
        elif function_name is None:
            return None
        else:
            err_msg = "Function '{}' is unknown.".format(function_name)
            raise ValueError(err_msg)

    @staticmethod
    def _append_params(name, param_values, dependency, index, fitting_values):
        """
        Distributions are being fitted and the results are appended to param_points

        Parameters
        ----------
        name : str,
            name of distribution (Weibull, Lognormal, Normal, KernelDensity (no dependency))

        param_values : list,
            contains lists that contain values for each param : order (shape, loc, scale)

        dependency : list,
            Length of 3 in the order (shape, loc, scale) contains :
            None -> no dependency
            int -> depends on particular dimension

        index : int,
            order : (shape, loc, scale) (i.e. 0 -> shape)

        fitting_values : list,
            values that are used to fit the distribution


        """

        # fit distribution
        current_params = Fit._fit_distribution(fitting_values, name)
        for i in range(index, len(dependency)):
            # check if there is a dependency and whether it is the right one
            if dependency[i] is not None and \
                            dependency[i] == dependency[index]:
                # calculated parameter is appended to param_values
                param_values[i].append(current_params[i])

    @staticmethod
    def _get_fitting_values(sample, samples, name, dependency, number_of_steps, index):
        """
        Returns values for fitting.

        Parameters
        ----------
        sample : list,
            data to be fit

        samples : list,
            List that contains data to be fitted : samples[0] -> first variable (i.e. wave height)
                                                   samples[1] -> second variable
                                                   ...

        name : str,
            name of distribution (Weibull, Lognormal, Normal, KernelDensity (no dependency))

        dependency : list,
            Length of 3 in the order (shape, loc, scale) contains :
                None -> no dependency
                int -> depends on particular dimension

        number_of_steps : int,
            number of distributions used to fit shape, loc, scale

        index : int,
            order : (shape, loc, scale) (i.e. 0 -> shape)

        """

        # compute steps
        steps, step_size = np.linspace(min(samples[dependency[index]]), max(samples[dependency[index]]),
                                       num=number_of_steps, endpoint=False, retstep=True)
        steps += 0.5 * step_size
        # sort samples
        samples = np.stack((sample, samples[dependency[index]])).T
        sort_indice = np.argsort(samples[:, 1])
        sorted_samples = samples[sort_indice]
        # return values
        param_values = [[], [], []]
        dist_values = []
        # look for data that is fitting to each step
        for i, step in enumerate(steps):
            mask = ((sorted_samples[:, 1] >= step - 0.5 * step_size) & (sorted_samples[:, 1] < step + 0.5 * step_size))
            fitting_values = sorted_samples[mask, 0]
            try:
                # fit distribution to selected data
                Fit._append_params(name, param_values, dependency, index, fitting_values)
                dist_values.append(fitting_values)
            except ValueError:
                # for case that no fitting data for the step has been found -> step is deleted
                steps = np.delete(i, steps)
                warnings.warn(
                    "There is not enough data for step '{}' in dimension '{}'. This step is skipped. "
                    "Maybe you should ckeck your data or reduce the number of steps".format(step, dependency[index]),
                    RuntimeWarning, stacklevel=2)
        return steps, dist_values, param_values

    @staticmethod
    def _get_distribution(dimension, samples, **kwargs):
        """
        Returns the fitted distribution, the dependency and the points for plotting the fits.

        Parameters
        ----------
        sample : list,
            entry in samples for the particular dimension (i.e. samples[0])

        samples : list,
            List that contains data to be fitted : samples[0] -> first variable (i.e. wave height)
                                                   samples[1] -> second variable
                                                   ...

        """

        # save settings for distribution
        sample = samples[dimension]
        name = kwargs.get('name', 'Weibull')
        dependency = kwargs.get('dependency', (None, None, None))
        functions = kwargs.get('functions', ('polynomial', 'polynomial', 'polynomial'))
        number_of_steps = kwargs.get('n_steps')

        # handle KernelDensity separated
        if name == 'KernelDensity':
            if dependency != (None, None, None):
                raise NotImplementedError("KernelDensity can not be conditional.")
            return KernelDensityDistribution(Fit._fit_distribution(sample, name)), dependency, [
                [sample], [sample], [sample]], [None, None, None]

        # points for plotting the fits
        param_points = [None, None, None]
        dist_points = [None, None, None]

        # initialize params (shape, loc, scale)
        params = [None, None, None]

        for index in range(len(dependency)):

            # continue if params is yet computed
            if params[index] is not None:
                continue

            if dependency[index] is None:
                # case that there is no dependency for this param
                current_params = Fit._fit_distribution(sample, name)
                for i in range(index, len(functions)):
                    # check if the other parameters have also no dependency
                    if dependency[i] is None:
                        if i == 2 and name == 'Lognormal_2':
                            params[i] = np.log(current_params[i])
                        else:
                            params[i] = current_params[i]
                        dist_points[i] = [sample]
            else:
                # case that there is a dependency
                steps, dist_values, param_values = Fit._get_fitting_values(
                    sample, samples, name, dependency, number_of_steps, index)

                for i in range(index, len(functions)):
                    # check if the other parameters have the same dependency
                    if dependency[i] is not None and dependency[i] == dependency[index]:
                        if i == 2 and name == 'Lognormal_2':
                            fit_points = [np.log(p(None)) for p in param_values[i]]
                        else:
                            fit_points = [p(None) for p in param_values[i]]
                        # fit params with particular function
                        try:
                            param_popt, param_pcov = curve_fit(
                                Fit._get_function(functions[i]),
                                steps, fit_points)
                        except RuntimeError:
                            # case that optimal parameters not found
                            if i == 0 and name == 'Lognormal_2':
                                param_name = "sigma"
                            elif i == 2 and name == 'Lognormal_2':
                                param_name = "mu"
                            elif i == 0:
                                param_name = "shape"
                            elif i == 1:
                                param_name = "loc"
                            elif i == 2:
                                param_name = "scale"

                            warnings.warn(
                                "Optimal Parameters not found for parameter '{}' in dimension '{}'. "
                                "Maybe switch the given function for a better fit. "
                                "Trying again with a higher number of calls to function '{}'."
                                "".format(param_name, dimension, functions[i]), RuntimeWarning,
                                stacklevel=2)
                            try:
                                param_popt, param_pcov = curve_fit(
                                    Fit._get_function(functions[i]),
                                    steps, fit_points, maxfev=int(1e6))
                            except RuntimeError:
                                raise RuntimeError(
                                    "Can't fit curve for parameter '{}' in dimension '{}'. "
                                    "Number of iterations exceeded.".format(param_name, dimension))
                        # save fitting points
                        param_points[i] = (steps, fit_points)
                        dist_points[i] = dist_values
                        # save param
                        params[i] = FunctionParam(*param_popt, functions[i])

        # return particular distribution
        if name == 'Weibull':
            return WeibullDistribution(*params), dependency, dist_points, param_points
        elif name == 'Lognormal_2':
            return LognormalDistribution(sigma=params[0], mu=params[2]), dependency, dist_points, param_points
        elif name == 'Lognormal_1':
            return LognormalDistribution(*params), dependency, dist_points, param_points
        elif name == 'Normal':
            return NormalDistribution(*params), dependency, dist_points, param_points


if __name__ == "__main__":
    import doctest
    doctest.testmod()
    # fit data by creating a Fit object