# Wheanut — 90-second demo

**0–15 seconds — problem**
“From space, corn harvested for silage and grain can look similar. Wheanut helps farmers and analysts inspect seasonal evidence, understand a model's prediction and identify what needs field verification.”

**15–40 seconds — show the product**
Open AI Analysis. Choose BARC field 1, 2021, and open its report. “We trained our own harvest classifier on real Sentinel-2 observations. NVIDIA Nemotron runs locally on the team GPU and turns the result into a short explanation. These are saved historical reports; we do not claim this button runs live inference.”

**40–60 seconds — map and evidence**
Click View this field on the map. Change season, select a field, inspect its NDVI, add a review note. “These are actual research boundaries and cloud-masked observations. NDVI measures greenness; it cannot establish harvest type on its own. Our interface keeps predictions separate from reference labels.”

**60–80 seconds — evaluation**
Open Data & reports. “We evaluated 44 field-years with both year and field held out. Accuracy is 68.2%, balanced accuracy 70.3%, and Silage recall 75%. Silage precision is only 45%, so false positives are a real limitation. Overall accuracy is below the 72.7% majority baseline; we show this openly.”

**80–90 seconds — next**
“Our next step is more labeled fields and a live inference backend. Teammates can replace the model adapter without rebuilding the frontend. Wheanut supports evidence review, not advice on when to harvest.”
