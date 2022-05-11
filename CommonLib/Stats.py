"""
.. module:: Stats
    :platform: Unix, Windows
    :synopsis: Statistics methods and extensions.
.. moduleauthor:: Albert Ferguson <albertferguson@propertyme.com>
"""

from math import ceil, sqrt

import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
from pandas import DataFrame, Series
from sklearn import preprocessing


def confidence_interval(std_pop: float, n: int, z_star: float) -> float:
    return z_star * (std_pop/np.sqrt(n))

def simple_stats(self, columns, statsToView=["mean", "std", "min", "max"]):
    """Simplify the describe functionality and assign more useful stats.
    
    **params represents the stats to utilise from the built-in describe function.

    Assign this handle to a dataframe field of the same name to call it on dataframes!
    """
    n = self.index.nunique()
    
    _describe = (self[columns]
        .describe()
        .reset_index()
    )

    # Calc the CI and estimate the population mean of each proc value
    # for a CI interval of 95% => Z* = 1.96
    # Delta Degrees of Freedom = 0 uses the pop. std formula.

    _std_pop = DataFrame(self[columns].std(ddof=0), columns=["std (pop)"])
    _95ci = DataFrame(_std_pop
        .copy()
        .apply(lambda col: 
               confidence_interval(col, n, z_star=1.96))
        .rename(columns={"std (pop)": "95CI"})
    )
    _90ci = DataFrame(_std_pop
        .copy()
        .apply(lambda col: 
               confidence_interval(col, n, z_star=1.645))
        .rename(columns={"std (pop)": "90CI"})
    )
    
    _describe = (_describe
        .loc[_describe["index"]
        .isin(statsToView)]
        .set_index("index")
        .unstack().unstack()
        # add any custom stats here
        .join(_std_pop)
        .join(_95ci)
        .join(_90ci)
        # the join creates a series, re "unstack" to reset
        .unstack().unstack()
    )
    
    return _describe

def base_line(self, column, n: int) -> Series:
    """Baseline value to compare against. 
    
    Assign this handle to a dataframe field of the same name to call it on dataframes!
    """

    if n <= 1:
        raise ValueError("number of elements to fill a 1D series with must be at least 2!")

    return Series(np.full((1, n), self[column].mean())[0])

def datetime_to_sec(self, column) -> Series:
    """Get a datetime column's seconds values.

    Assign this handle to a dataframe field of the same name to call it on dataframes!
    """
    
    return Series([ith.second for ith in self[column].view()])

def standardise_scale(self, **params) -> DataFrame:
    """Standardise a dataframe's scale and return a new dataframe on a similar index.

    **params are passed to the sklearn StandardScaler instance.

    Assign this handle to a dataframe field of the same name to call it on dataframes!
    """

    std_scaler = preprocessing.StandardScaler()
    newColNames = [f"{col}_std_scale" for col in self.columns.tolist()]
    _copy = self.copy().values.transpose()
    _indexName = self.index.name
    _index = self.index

    stdDataframe = (DataFrame(
        std_scaler.fit_transform(_copy, **params).transpose(), columns=newColNames)
            .assign(**{_indexName: _index})
            .set_index(_indexName)
    )

    return stdDataframe

def categorical_hist(self, column, by, layout=None, legend=None, **params):
    """Plot a categorical histogram column by "category".

    Assign this handle to a dataframe field of the same name to call it on dataframes!
    """

    # http://themrmax.github.io/2015/11/13/grouped-histograms-for-categorical-data-in-pandas.html
    # This was a great read and did exactly what I wanted here!
    
    if layout == None:
        s = ceil(sqrt(self[column].unique().size))
        layout = (s,s)

    return (self.groupby(by)[column]
               .value_counts()
               .sort_index()
               .unstack()
               .plot.bar(subplots=True, layout=layout, legend=legend, rot=0, **params)
               )

def Integer_ZDistribution(mu: float, sigma: float, n: int, negativeDist=False, filterOutputRange: tuple=()) -> list:
    """Create an integer Z-Distribution (Normal) with mean mu and std deviation sigma.

    Args
    ----
    mu: float
        The mean of the desired distribution.
    sigma: float
        The standard deviation of the desired distribution.
    n: int
        The number of samples in the returned sample distribution.

    Kwargs
    ------
    negativeDist: bool
        Return the distribution, but all values are negative,
        i.e. map foo(-1 * k) across all elements.
    filterOutputRange: tuple(int, int)
        Filter the output between a min-max value range (inclusive).
        If a limit is found, the value is replaced via its neighbour.

        e.g.

        (-1, -8):
            lower: -1 is replaced with -2
            upper: -8 is replaced with -7
        Hence,
        The output will be on the range (-1, -8).

        If you desired a non-inclusive range, add 1 to each limit,
        The output would then be in the range [-1, -8] inclusive.
    """
    
    zdist = np.random.normal(mu, sigma, n).astype(int)

    if (negativeDist):
        zdist = np.negative(zdist)

    # apply a min-max filter
    if len(filterOutputRange) != 0:
        lowerFilter = filterOutputRange[0]
        upperFilter = filterOutputRange[1]

        # When finding the value, replace with the value
        zdist = np.where(zdist >= lowerFilter, lowerFilter - 1, zdist)
        zdist = np.where(zdist <= upperFilter, upperFilter + 1, zdist)
    # cast the output to int from np.int32
    # use the list method cast to avoid accidentally converting back to a list of np.int32's
    return zdist.astype(int).tolist()

def GraphHistogramWithOverlay(X: list, title: str, discrete: bool=True) -> None:
    """Graph a histogram of an arraylike input.

    Args
    ----
    X: list, arraylike input of numbers
        The input to graph.
    title: str
        Graph title.

    Kwargs
    ------
    discrete: boolean
        Remove "gaps" in the histogram when dealing with integer data-sets.
    """

    fig, ax = plt.subplots(1)
    sns.histplot(data=X, ax=ax, discrete=discrete, kde=True, element="bars", cbar=True)
    ax.set_title(f"Histogram of {title}")
    plt.show()
    return

def corr_heatmap(self, ax, sig_measure: float, sample_perc: float=0.3, **params) -> bool:
    """If any linear correlations exist on the frame, display them as a heatmap.

    **params are passed to the Seaborn heatmap handle.

    Assign this handle to a dataframe field of the same name to call it on dataframes!
    """

    corrs = self.copy().sample(frac=sample_perc).dropna().corr()

    if not corrs.empty:
        # filter corrs for significance >= to ...
        sns.heatmap(
            corrs[(corrs >= sig_measure) | (corrs <= -1 * sig_measure)], 
            linewidths=.8,
            ax=ax,
            **params
        )

        return True
    
    print("No corrs were determined to be valid.")
    return False
