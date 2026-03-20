import pandas as pd
import plutofullassessdef as pfadef
import plutofullassesssdata as pdata
import pathlib
import os

# Create data dir
pathlib.Path("./test_data").mkdir(exist_ok=True)

# Create a dummy protocol file with HOC as next task
subjid = "test_subj"
stype = "stroke"
limb = "RIGHT"
filename = f"./test_data/{subjid}_{stype}_{limb}_protocol.csv"

# Mock the protocol file
# We'll create it with FPS tasks completed
df = pd.DataFrame(columns=pfadef.FA_SUMMARY_HEADER)
# Add some tasks
df = pd.concat([df, pd.DataFrame([{
    "session": "sess1",
    "mechanism": "FPS",
    "task": "AROM",
    "ntrial": 3,
    "status": "Complete"
}, {
    "session": None,
    "mechanism": "HOC",
    "task": "AROM",
    "ntrial": 3,
    "status": "Incomplete"
}])], ignore_index=True)
df.to_csv(filename, index=False)

try:
    p = pdata.PlutoAssessmentProtocolData(subjid, stype, limb, limb, limb, "./test_data", "./test_data/sess")
    print(f"Current index: {p.index}")
    print(f"Current next mech: {p.df.iloc[p.index]['mechanism'] if p.index is not None else 'None'}")
    
    print("Trying to set mechanism to FPS (already completed)...")
    p.set_mechanism("FPS")
    print("Successfully set mechanism to FPS!")
    
    print(f"Enabled tasks for FPS: {p.task_enabled}")
    
    print("Trying to set task to AROM for FPS...")
    p.set_task("AROM")
    print("Successfully set task to AROM for FPS!")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
finally:
    if os.path.exists(filename):
        os.remove(filename)
