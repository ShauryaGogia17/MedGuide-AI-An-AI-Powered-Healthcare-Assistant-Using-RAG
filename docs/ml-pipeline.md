# Lab analysis

Each PDF page is extracted using the configured OpenAI model with a strict schema. Pydantic validates finite values, names, units, bounds, page numbers, and exact evidence snippets. Unverified pages contribute warnings. The application never guesses a missing unit, interval, date, or numeric result.

Dated observations are grouped by normalized test name and unit. Numeric reference-range comparisons use the printed bounds and inclusive/exclusive endpoints; missing ranges remain unclassified. Undated observations still receive range comparisons but are excluded from trends and charts. Missing units suppress trend labels.

Linear regression fits values against actual elapsed days. Increasing/decreasing/stable are descriptive directions. Stability uses a 1% normalized fitted-change tolerance; this is not a medical threshold. Percent change compares the first and last dated values, with an unavailable result when the first value is zero. At least two different dates are required.

Historical z-scores use only earlier readings, at least eight baseline measurements, and nonzero sample variance. A flag describes a statistical departure, never a diagnosis. Statistical flags do not substitute for the printed reference interval. Measurements may still be incomparable across laboratory methods, preparation, or changing reference ranges.
