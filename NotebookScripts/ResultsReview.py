#!/usr/bin/env python
# coding: utf-8

# # Results Review
# 
# Review the results of the load testing.
# 
# 
# ## Prerequisites:
# --------------------
# 
# TBD
# 
# ## Workflow:
# --------------------
# 
# Steps 1 - 3 consitute the ETL stage of this workflow. 4 includes any required processing to create the following variables,
# * `gross execution`
# * `deadtime`
# * `planning time`
# * `net execution`
# 
# Step 5. onwards pertains to the review of processing in step 4.
# 
# 1. Set Constants;
# 2. Ingest:
#   * (Optional) From db and save to raw file,
#   * Read from raw file.
#      * Apply typing to dimensions on ingest.
# 3. Overview Raw Data;
#   * Quick stats,
#   * Scatters,
#   * Categorical histograms (quickly check status of runs).
# 4. Raw Data Processing;
# 5. Processed Data Review.

# In[ ]:


import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from sklearn.preprocessing import normalize
import seaborn as sns
import numpy as np
import pandas as pd
from pandas import DataFrame, Series
from sklearn import preprocessing

from datetime import datetime
import requests as r
from tqdm.auto import tqdm

from CommonLib import NotebookHelper, Stats, ConsoleHelpers
from CommonLib.Time import FunctionExecutionTimer
from Config import (ConfigureCsvFilename, ConfigureDbTableName,
                    ConfigureMySqlConnectionString, ConfigurePropertyMeBaseUrl)
from Database.ContextBox import GetConnection, DatabaseConnection


# ## 1. Constants Assigned
# --------------------

# In[ ]:


#constants
baseUrl = ConfigurePropertyMeBaseUrl()

default_ltUsersDeepFn = 'deepuser-aa-load-test-customer-data'
default_ltUsersWideFn = 'wideuser-aa-load-test-customer-data'

default_ltAutomationsDeepFn = 'deepuser-aa-load-test-inserted-automations-for-adc60273-a326-411f-8442-8503cbd5bab2'
default_ltAutomationsWideFn = 'wideuser-aa-load-test-inserted-automations-for-adc60278-030e-4c80-9410-a3799f5f5bb9'

default_rawDataDeepFn = 'deep-aa-load-test-raw-data'
default_rawDataWideFn = 'wide-aa-load-test-raw-data'

dbString = ConfigureMySqlConnectionString()

dateTimeCols = [
    "Automation Last Run Status As Of",
    "Run Created On",
    "Last Run Status On", 
    "RunStep Created On"
]

categoricalCols = [
    "Automation Run Status",
    "Automation Status"
]

boolCols = ["Any Run Step Failed"]

dtypes = {
    "CustomerId": "object",
    "AutomationId": "object",
    "Any Run Step Failed": "boolean",
}

for col in categoricalCols:
    dtypes[col] = "category"

for col in boolCols:
        dtypes[col]= "boolean"

# graph config
plt.style.use('seaborn-notebook')
plt.rcParams['figure.figsize'] = [20, 5]
sns.set_palette("Paired")


# In[ ]:


ltDeepUsersFn = None
ltWideUsersFn = None

ltAutomationsDeepFn = None
ltAutomationsWideFn = None

rawDataDeepFn = None
rawDataWideFn = None

rawDataDeep = None
rawDataWide = None

customerDeep = None
customerWide = None


# ## 2. Raw Data Ingest
# --------------------

# In[ ]:


print("********************************************************************************")
print('\nLOADING DEEP (BASELINE) AND WIDE LOAD-TESTING CUSTOMERS:')

# This is always called. 
# We do not re-read customer data from the database again, as this should have 
# been completed in prev testing setup-and-run steps.
csvExplanation = """
    The csv will require columns titled: CustomerId, Username, Pw, MessageTemplateId
    If these values are missing, then subsequent operations may fail unexpectedly."""
    
print("== CONFIGURING LOAD TESTING CUSTOMER CSV DATA ==")
print(csvExplanation)

if not ltDeepUsersFn:
    print("== DEEP USER ==")
    ltDeepUsersFn = ConfigureCsvFilename(default_ltUsersDeepFn)
    
if not ltWideUsersFn:
    print("== WIDE USERS ==")
    ltWideUsersFn = ConfigureCsvFilename(default_ltUsersWideFn)
    
if not ltAutomationsDeepFn:
    print("== DEEP AUTOMATION ==")
    ltAutomationsDeepFn = ConfigureCsvFilename(default_ltAutomationsDeepFn)
    
if not ltAutomationsWideFn:
    print("== WIDE AUTOMATIONS ==")
    ltAutomationsWideFn = ConfigureCsvFilename(default_ltAutomationsWideFn)
    
# Read from csv (expecting 4 columns)
print('\nREADING LOAD TESTING CUSTOMER DATA:')

# sequential automation runs
automationsDeep = (pd
    .read_csv(ltAutomationsDeepFn)
    .drop(["ScheduleExists", "Unnamed: 0"], axis=1, errors="ignore")
)

# the deep test user
deepUser = (pd
    .read_csv(ltDeepUsersFn)
    .drop(["Unnamed: 0"], axis=1, errors="ignore")
)

# propogate customerDeep across the all of the deep automation runs.
customerDeep = (automationsDeep
    .copy()
    .assign(CustomerId=deepUser.CustomerId.values[0])
    .assign(Username=deepUser.Username.values[0])
    .assign(Pw=deepUser.Pw.values[0])
    .assign(MessageTemplateId=deepUser.MessageTemplateId.values[0])
    .assign(MemberId=deepUser.MemberId.values[0])
)

# if we only have 1 automation this will throw an error
# ie if you preemptively called this script before the deep test completes.
NotebookHelper.Output(customerDeep.sample(n=3, replace=True))

# simulataneous automation runs
automationsWide = (pd
    .read_csv(ltAutomationsWideFn)
    .drop(["ScheduleExists", "Unnamed: 0"], axis=1, errors="ignore")
)

# the wide test user
wideUser = (pd
    .read_csv(ltWideUsersFn)
    .drop(["Unnamed: 0"], axis=1, errors='ignore')
)

# propogate customerWide across the all of the wide automations.
customerWide = (automationsWide
    .copy()
    .assign(CustomerId=wideUser.CustomerId.values[0])
    .assign(Username=wideUser.Username.values[0])
    .assign(Pw=wideUser.Pw.values[0])
    .assign(MessageTemplateId=wideUser.MessageTemplateId.values[0])
    .assign(MemberId=wideUser.MemberId.values[0])
)

NotebookHelper.Output(customerWide.sample(n=3))

print("********************************************************************************")


# In[ ]:


# Wrap this function with a db conn accessor
@DatabaseConnection()
def GetResults(dbString: str, automationIds: list[str]) -> pd.DataFrame:
    _conn = GetConnection(dbString) # via accessor to ContextBox
    autoIds_str = ','.join(f"'{auto}'" for auto in automationIds)
    
    sqlString = """
    SELECT
        a.CustomerId, ar.AutomationId,
        ar.AnyStepFailed `Any Run Step Failed`, ar.`Status` `Automation Run Status`, a.`Status` `Automation Status`,
        a.LastRunStatusOn `Automation Last Run Status As Of`, 
        ar.CreatedOn `Run Created On`, ar.StatusOn `Last Run Status On`,
        ars.CreatedOn `RunStep Created On`
    FROM automation AS a 
    LEFT JOIN automationrun AS ar 
        ON ar.AutomationId = a.Id
    LEFT JOIN automationrunstep AS ars 
        ON ars.AutomationRunId = ar.Id 
    WHERE a.Id IN ({}) ORDER BY ars.CreatedOn;""".format(autoIds_str)
        
    df = pd.read_sql(sqlString, _conn);
    return df


# In[ ]:


# Retrieve the baseline (deep test) run data
print("********************************************************************************")
print('\nLOADING DEEP (BASELINE) AND WIDE RAW DATA:')

while True:
    # Ask if want to connect to db or skip straight to reading from a csv file
    question = "Obtain data from SQL db? Type 'y' to use config'd credentials or 'n' to read from a previously saved csv input: "
    answer = input(question).lower().strip()
    
    # if not 'Enter' or whitespace
    if (len(answer.strip()) != 0):
        break

if (answer == 'y'):
    print("A csv will be generated from this db read and cached for subsequent uses of this script.")
    print("Chose 'n' in the previous step to use this csv next time.")

    if not rawDataDeepFn:
        print("== DEEP ==")
        rawDataDeepFn = ConfigureCsvFilename(default_rawDataDeepFn)

    if not rawDataWideFn:
        print("== WIDE ==")
        rawDataWideFn = ConfigureCsvFilename(default_rawDataWideFn)
    
    # retrieve the raw data (exclude any results where an automationId is NaN / None / Null
    if not customerDeep.empty and "AutomationId" in customerDeep.columns:
        validCustomers = customerDeep.dropna()
        if len(customerDeep) > 0:
            rawDataDeep = GetResults(dbString, validCustomers.AutomationId.tolist()).set_index(["AutomationId", "CustomerId"])
    else:
        print("No valid customer automations could be found from the preloaded data.")
        deeptestAutoId = input("Enter a deeptest automation ID to manually search for results: ").strip().lower()
        answer = input(f"{deeptestAutoId}\tIs this ID correct? ").strip().lower() == 'y'
        while not answer:
            deeptestAutoId = input("Enter a deeptest automation ID to manually search for results: ").strip().lower()
            answer = input(f"{deeptestAutoId}\tIs this ID correct? ").strip().lower() == 'y'
            
        rawDataDeep = GetResults(dbString, [deeptestAutoId]).set_index("CustomerId")
    
    # retrieve the raw data (exclude any results where an automationId is NaN / None / Null
    if "AutomationId" in customerWide.columns:
        validCustomers = customerWide.dropna()
        if len(customerWide) > 0:
            rawDataWide = GetResults(dbString, validCustomers.AutomationId.tolist()).set_index(["AutomationId", "CustomerId"])
    
    if rawDataDeep is None:
        input("No DEEP data was obtained from the db. No csv file was created! CHECK INPUTS AND RETRY.")
    elif rawDataWide is None:
        input("No WIDE data was obtained from the db. No csv file was created! CHECK INPUTS AND RETRY.")
    else:
        # sample randomly parses, so output will vary from run-to-run
        NotebookHelper.Output(rawDataDeep.sample(n=5))
        NotebookHelper.Output(rawDataWide.sample(n=5))
        
        # save output to avoid repeatedly accessing the db
        rawDataDeep.to_csv(rawDataDeepFn)
        rawDataWide.to_csv(rawDataWideFn)
        
        # overwrite with the save and type dimensions as we go
        rawDataDeep = pd.read_csv(rawDataDeepFn, dtype=dtypes, parse_dates=dateTimeCols, infer_datetime_format=True)
        rawDataWide = pd.read_csv(rawDataWideFn, dtype=dtypes, parse_dates=dateTimeCols, infer_datetime_format=True)
else: 
    print("== READING CSV DATA ==")
    
    if not rawDataDeepFn:
        print("== DEEP ==")
        rawDataDeepFn = ConfigureCsvFilename(default_rawDataDeepFn)

    if not rawDataWideFn:
        print("== WIDE ==")
        rawDataWideFn = ConfigureCsvFilename(default_rawDataWideFn)
    
    print('\nREADING DATA:')
    
    rawDataDeep = pd.read_csv(rawDataDeepFn, dtype=dtypes, parse_dates=dateTimeCols, infer_datetime_format=True).set_index(["AutomationId", "CustomerId"])
    rawDataWide = pd.read_csv(rawDataWideFn, dtype=dtypes, parse_dates=dateTimeCols, infer_datetime_format=True).set_index(["AutomationId", "CustomerId"])
    
    print(f"\t{len(rawDataDeep)} DEEP Samples")
    print(f"\t{len(rawDataWide)} WIDE Samples")
    
    # sample randomly parses, so output will vary from run-to-run
    NotebookHelper.Output(rawDataDeep.sample(n=5))
    NotebookHelper.Output(rawDataWide.sample(n=5))
    
print("********************************************************************************")


# ## 3. Overview of Raw Data
# --------------------

# Results are returned with unique runsteps - this is "bloat" raw data with several constants (ids). What we actually require is a dataframe that shows the min, max and avg values of RunStep Created On. However, it would also be useful to review runsteps before aggregation, as it's distribution may yield further information.

# In[ ]:


rawSecondsCols = list()

def time_to_ns_int64(df, columns):
    '''
    Change columns to np.int64 (ie nano seconds).
    '''
    
    global rawSecondsCols
    rawSecondsCols = [f"{col} - Seconds" for col in dateTimeCols]
    
    df = df.copy()
    def converter(col):
        return col.astype(np.int64)
    
    convertedFrame = (
        df[columns]
            .apply(converter)
            .rename(columns=dict(zip(columns, rawSecondsCols)))
            #.pipe(lambda col: col * 1e-9) # convert to seconds
        )
    
    return pd.concat([df, convertedFrame], axis='columns') 

# 1. It seems common that we need to review the data in seconds, let's save this as a new Column.
rawDataDeep = rawDataDeep.pipe(time_to_ns_int64, dateTimeCols)
rawDataWide = rawDataWide.pipe(time_to_ns_int64, dateTimeCols)

# 2. extension assigned
pd.DataFrame.categorical_hist = Stats.categorical_hist


# In[ ]:


# 1. Output the table DEEP overviews
print("== DEEP ==")
NotebookHelper.Output(rawDataDeep.dtypes)
NotebookHelper.Output(rawDataDeep.describe(include=["datetime64[ns]", "boolean"], datetime_is_numeric=True))
NotebookHelper.Output(rawDataDeep.sample(n=3))
NotebookHelper.Output(rawDataDeep[dateTimeCols].sample(n=3))

# 1. Output the table WIDE overviews
print("== WIDE ==")
NotebookHelper.Output(rawDataWide.dtypes)
NotebookHelper.Output(rawDataWide.describe(include=["datetime64[ns]", "boolean"], datetime_is_numeric=True))
NotebookHelper.Output(rawDataWide.sample(n=3))
NotebookHelper.Output(rawDataWide[dateTimeCols].sample(n=3))


# In[ ]:


# 2. Determine any potential correlations
Stats.GraphCorrHeatmap(rawDataDeep[dateTimeCols], 0.8)
Stats.GraphCorrHeatmap(rawDataWide[dateTimeCols], 0.8)

# 3. YOLO a scatter and see what we find
axes = []
# without random sampling
axes.append(rawDataWide
    .reset_index()
    .set_index("AutomationId")[dateTimeCols]
    .plot())

# with random sampling
axes.append(rawDataWide
    .reset_index()
    .set_index("AutomationId")[dateTimeCols]
    .sample(frac=0.2)
    .plot())

for ax in axes:
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=5)
    ax.legend(loc="center right", framealpha=0.9)


# ### Status Overview
# --------------------

# In[ ]:


statusframe = pd.DataFrame({
    "WIDE Auto Runs Count" : rawDataWide.groupby(["Automation Run Status"]).size(),
    "WIDE Automations" : rawDataWide.groupby(["Automation Status"]).size(),
    "DEEP Auto Runs" : rawDataDeep.groupby(["Automation Run Status"]).size(),
    "DEEP Automations" : rawDataDeep.groupby(["Automation Status"]).size()
}).reset_index().rename(columns={"index": "Status"}).set_index("Status")

statusframe.plot(kind="barh", stacked=True)
sns.despine(left=False, bottom=True)


# In[ ]:


display(rawDataWide)


# In[ ]:


# Let's look at the density of run and runstep created on events.

x_runstep = rawDataWide["RunStep Created On"].view().sort_values().unique()
x_run = rawDataWide["Run Created On"].view().sort_values().unique()
x_times = [x_runstep, x_run]

runstepKdeFig1, timePlotAx = plt.subplots()
runstepKdeFig2, timePlotAxes2 = plt.subplots(1, 2)

sns.kdeplot(data=rawDataWide.reset_index(), x="RunStep Created On", ax=timePlotAx)
sns.kdeplot(data=rawDataWide.reset_index(), x="Run Created On", ax=timePlotAx)

sns.kdeplot(data=rawDataWide.reset_index(), x="RunStep Created On", ax=timePlotAxes2[0])
sns.kdeplot(data=rawDataWide.reset_index(), x="Run Created On", ax=timePlotAxes2[1])

runstepKdeFig1.suptitle("Time analysis Time KDE - Fig 1")
runstepKdeFig1.legend(dateTimeCols, loc="upper right")

runstepKdeFig2.suptitle("Time analysis Time KDE - Fig 2")
runstepKdeFig2.legend(dateTimeCols, loc="upper right")

timePlotAx.set_xticklabels(labels=x_times[i], rotation=0, ha='right')

for i, ax in enumerate(timePlotAxes2):
    ax.set_xticklabels(labels=x_times[i], rotation=45, ha='right')


# ## 4. Raw Data Processing
# --------------------
# 
# ### Building the Processed Data
# 
# #### gross proc
# 
# `gross_exec = FinalisedStatusOn - FirstRunStepCreated`
# 
# #### deadtime
# 
# `deadtime = FirstRunStepCreated - RunCreatedOn`
# 
# #### planning time
# 
# Currently we are missing any logging of first precondition finishing execution!
# 
# `planningtime =  LastRunStepCreated - FirstRunStepCreated`
# 
# #### net proc
# 
# Net execution is a simple summation,
# 
# `net_exec = FinalisedStatusOn - RunCreatedOn`
# 
# 
# #### Net Runstep Time
# 
# `net_step_time = FinalisedStatusOn - LastRunStepCreated`
# 
# However, given the minimal number of preconditions and minimial complexity in validating them, we can assume that:
# `PreconditionFinished - LastUnskippedRunStarted -> 0`
# ` => planningtime ~ deadtime`
# ` => net_exec = gross_exec - planningtime` or `=> net_exec = gross_exec - deadtime`

# In[ ]:


procCols = [
    "GrossProc",
    "DeadTime",
    "PlanningTime",
    "NetRunStepTime",
    "NetProc"
]

secondsProcCols = []
normProcCols = []

def BuildProcDf(rawFrame: pd.DataFrame, collapse=False):
    global secondsProcCols
    global normProcCols
    
    # For normalising
    std_scaler = preprocessing.StandardScaler()
    
    # 1. We need to reduce the dataframe that we are working with, but we will need both the seconds
    #    as well as timestamp dtype'd cols. So it'll be doubled up for the moment.
    procFrame = (
        # limit the columns to proc on - ie drop the categorical and boolean dtype's.
        rawFrame
            .copy()
            .reset_index()[dateTimeCols + rawSecondsCols + ["AutomationId"]]
            .set_index("AutomationId")
            # 2. These min-max vals are important to several calc's. Add them as separate columns.
            .assign(LastRunStepCreated=rawFrame["RunStep Created On"].max())
            .assign(FirstRunStepCreated=rawFrame["RunStep Created On"].min())
        )

    # 3. If we have multiple runs of a test - then we need to aggregate or "collapse"
    if collapse:
        # numeric_only avoids loss of timedelta data
        # https://github.com/pandas-dev/pandas/issues/5724
        procFrame = (
            procFrame
                .groupby("AutomationId")
                .mean(numeric_only=False) 
        )
    
    # 4. Apply the processing and update the frame as we go.
    procFrame = (
        procFrame
            .assign(GrossProc=procFrame["Automation Last Run Status As Of"] - procFrame["FirstRunStepCreated"])
            .assign(DeadTime=procFrame["FirstRunStepCreated"] - procFrame["Run Created On"])
            .assign(PlanningTime=procFrame["LastRunStepCreated"] - procFrame["FirstRunStepCreated"])
            .assign(NetProc=procFrame["Automation Last Run Status As Of"] - procFrame["LastRunStepCreated"])
            .assign(NetRunStepTime=procFrame["Automation Last Run Status As Of"] - procFrame["Run Created On"])
            .drop(dateTimeCols, axis=1)
    )
    
    # 5. Apply normalisations to some columns for easier comparison
    secondsProcCols = []
    normProcCols = []
    
    # Update the proc data to dtype int64
    for col in procCols:
        newName = f"{col} - Seconds"
        normProcCols.append(f"Normalised {col}")
        secondsProcCols.append(newName)
        # convert to seconds
        procFrame[newName] = procFrame[col].astype(np.int64)
    
    # 6. Combine these into our proc data...
    X_norm = (pd.DataFrame(
        std_scaler.fit_transform(procFrame[secondsProcCols].values.transpose()).transpose(), columns=normProcCols)
        .assign(AutomationId=procFrame.index)
        .set_index("AutomationId")
    )
    
    procFrame = pd.concat([procFrame, X_norm], axis=1)  
    
    return procFrame
    
deep = rawDataDeep.dropna()
if not deep.empty:
    procDataDeep = BuildProcDf(deep, collapse=True)

wide = rawDataWide.dropna()
if not wide.empty:
    procDataWide = BuildProcDf(wide)

# 4. Review this procdata to check for errors...
NotebookHelper.Output(procDataDeep.sample(n=1))
NotebookHelper.Output(procDataWide.sample(n=3))
NotebookHelper.Output(procDataWide.drop(secondsProcCols + normProcCols, axis=1).describe())


# ## 5. Processed Data Review
# --------------------

# In[ ]:


# Join up the deep and wide results for easier graphing - using normalised data

compframe1 = (procDataWide[normProcCols]
                  .copy()
                  .assign(Norm_GrossProc_Deep=procDataDeep["Normalised GrossProc"].values[0])
                  .assign(Norm_DeadTime_Deep=procDataDeep["Normalised DeadTime"].values[0])
                  .assign(Norm_PlanningTime_Deep=procDataDeep["Normalised PlanningTime"].values[0])
                  .assign(Norm_NetRunStepTime_Deep=procDataDeep["Normalised NetRunStepTime"].values[0])
                  .assign(Norm_NetProc_Deep=procDataDeep["Normalised NetProc"].values[0])
            )


# In[ ]:


# Join up the deep and wide results for easier graphing - this time using seconds

compframe2 = (procDataWide[secondsProcCols]
                  .copy()
                  .assign(Seconds_GossProc_Deep=procDataDeep["GrossProc - Seconds"].values[0])
                  .assign(Seconds_DeadTime_Deep=procDataDeep["DeadTime - Seconds"].values[0])
                  .assign(Seconds_PlanningTime_Deep=procDataDeep["PlanningTime - Seconds"].values[0])
                  .assign(Seconds_NetRunStepTime_Deep=procDataDeep["NetRunStepTime - Seconds"].values[0])
                  .assign(Seconds_NetProc_Deep=procDataDeep["NetProc - Seconds"].values[0])
            )


# In[ ]:


# Graph the proc data for comparison of a deep
figBarComp, compAxes = plt.subplots(1, 2, sharey=False)

figBarComp.suptitle("Processed Data Review - Run Aggregate Comps")

for ax in compAxes:
    ax.set_xticklabels(ax.get_xticks(), rotation=90)
    
sns.barplot(data=compframe1.sample(n=200), ax=compAxes[0], orient='h')
sns.barplot(data=compframe2.sample(n=200), ax=compAxes[1], orient='h')
sns.despine(left=False, bottom=True)


# In[ ]:


from datetime import datetime, timedelta

# Baseline value to compare against
def BaseLine(data, column, n, seconds=False):
    yMean = data[column].view().mean()
    if seconds:
        converted = yMean.seconds + yMean.microseconds * 1e-6
    else:
        # microseconds
        converted = yMean.seconds * 1e6 + yMean.microseconds
    baseline = np.full((1, n), converted)[0]
    return baseline

def NthRunData(data):
    return (procDataWide
                .groupby("AutomationId")
                .mean(numeric_only=False)
                .dropna()
           )


# In[ ]:


# 1. Setup the graphs and constants
n_wide_runs = procDataWide.index.nunique()
palette = sns.color_palette("mako_r", n_wide_runs)
palette = sns.color_palette("icefire", 5)
nthRunData = NthRunData(procDataWide)
dtNow = datetime.now()

ENABLE_DEEPTEST_LINE_OVERLAY = True

# number of wide runs, we want to view run-by-run
X = [i for i in range(n_wide_runs)]

# Setup the graphs
figResid_A, residAxes_TOP = plt.subplots(1, 2, sharey=False)
figResid_B, residAxes_BOTTOM = plt.subplots(1, 3, sharey=False)

figResid_A.suptitle("Gross and Net Processing - Inter-Run Baseline Comparison")
figResid_B.suptitle("Breakdown - Inter-Run Baseline Comparison")

labels_A = [
    "Mean GPT", # Gross Processing Time GPT
    "Mean NPT" # Net Processing Time NPT
]

labels_B = [
    "Mean DeadTime",
    "Mean Planning Time",
    "Mean NRST", # Net Run Step Time NRST
]

lineHandles = []

x_label = "Run Test No."
y_label_MS = "Time (seconds)"
y_label_S = "Time (seconds)"

figResid_A.text(0.5, 0.04, x_label, ha='center')
figResid_A.text(0.04, 0.5, y_label_MS, va='center', rotation='vertical')
figResid_B.text(0.5, 0.04, x_label, ha='center')
figResid_B.text(0.04, 0.5, y_label_S, va='center', rotation='vertical')

# 2. Add the data from the baseline
for i, baseline in enumerate(["GrossProc","NetProc"]):
    Y = BaseLine(procDataDeep, baseline, n_wide_runs, seconds=True)
    yMean = [(ith.seconds + ith.microseconds * 1e-6) for ith in nthRunData[baseline].view()]
    
    if ENABLE_DEEPTEST_LINE_OVERLAY:
        sns.lineplot(X, Y, 
                     color=palette.pop(), 
                     linestyle='dashed',
                     linewidth=3, 
                     ax=residAxes_TOP[i], 
                     label=labels_A[i])
        
    sns.scatterplot(x=X, y=yMean, ax=residAxes_TOP[i], hue=X)
    
for i, baseline in enumerate(["DeadTime","PlanningTime","NetRunStepTime"]):
    Y = BaseLine(procDataDeep, baseline, n_wide_runs, seconds=True)
    yMean = [(ith.seconds + ith.microseconds * 1e-6) for ith in nthRunData[baseline].view()]
    
    if ENABLE_DEEPTEST_LINE_OVERLAY:
        sns.lineplot(X, Y, 
                     color=palette.pop(), 
                     linestyle='dashed',
                     linewidth=3, 
                     ax=residAxes_BOTTOM[i], 
                     label=labels_B[i])
        
    sns.scatterplot(x=X, y=yMean, ax=residAxes_BOTTOM[i], hue=X)

for ax in residAxes_BOTTOM:
    handles, labels = ax.get_legend_handles_labels()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend().remove()
    
for ax in residAxes_TOP:
    handles, labels = ax.get_legend_handles_labels()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend().remove()

figResid_A.legend(loc="upper right", framealpha=1, frameon=False)
figResid_B.legend(loc="upper right", framealpha=1, frameon=False)

