## I. Grid Stress & Scarcity Risk (GSI)

*These questions identify the "when" and "how bad" of potential price spikes and scarcity events.*

1. **What is the peak probability of a Grid Stress Index (GSI) > 0.60 occurring in any hour over the next 14 days?**
2. **At what time does the P99 (extreme) Grid Stress Index peak over the seasonal horizon?**
3. **What is the probability of GSI exceeding 0.60 during the evening ramp (HB 17-20) for the next week?**
4. **Which specific ensemble paths show a GSI > 0.75 in the next 336 hours? (Identifying "Stress Scenarios")**
5. **How does the median (P50) GSI compare to the P90 GSI for the month of February?**
6. **What is the expected duration (hours) of GSI > 0.70 in the worst 5% of outcomes for a specific date?**
7. **On days with GSI > 0.70, what is the average `net_demand_plus_outages`?**
8. **What is the likelihood that `nonrenewable_outage_mw` exceeds 15,000 MW during a cold snap?**
9. **Identify the "Tightest Hour": The hour with the highest average GSI across all 1000 paths.**
10. **What is the probability of a GSI exceeding 0.65 longer than 4 consecutive hours?**

---

## II. Load & Temperature Sensitivity

*Understanding the primary driver of ERCOT demand: heating and cooling.*

11. **What is the P01 (Extreme Cold) temperature forecast for the 'rto' over the next 10 days?**
12. **In paths where RTO temperature drops below -5°C, what is the average total RTO Load?**
13. **Which load zone has the highest probability of seeing temperatures below 0°C next week?**
14. **What is the P99 RTO Load for the morning peak (HB 07-09) throughout February?**
15. **What is the correlation between `dew_2m` and `load` in the Houston zone (checking for humidity-driven demand)?**
16. **How much does P99 load increase for every 1°C drop in RTO temperature below 5°C?**
17. **What is the range (P99 - P01) of Load uncertainty for March 1st?**
18. **Identify paths where North Zone temperature is 5°C colder than the West Zone.**
19. **What is the probability of RTO Load exceeding 75,000 MW this winter?**
20. **During the lowest 1% of temperature outcomes, what is the median `nonrenewable_outage_mw`?**

---

## III. Renewables: The "Net" in Net Demand

*Solar and wind volatility are the main causes of intraday price swings.*

21. **What is the probability of "Dunkelflaute" (Wind Cap Factor < 5% AND Solar Cap Factor < 5%) during daylight hours?**
22. **What is the P10 (Low Wind) forecast for `wind_gen` during the evening ramp?**
23. **What is the expected solar ramp (MW change) between HB 07 and HB 09 in the P50 vs P90 scenarios?**
24. **In the West zone, what is the probability of `wind_100m_mps` dropping below 3 m/s (cut-in speed)?**
25. **How much `solar_gen` is at risk if GHI is 20% below the P50 forecast?**
26. **What is the maximum 1-hour downward wind ramp observed in any of the 1000 paths?**
27. **What is the probability that `solar_gen` contributes more than 15,000 MW during peak GSI hours?**
28. **Compare the variance of `wind_gen` vs `solar_gen` for the month of February.**
29. **Which ensemble path represents the "Maximum Renewable Curtailment Risk" (Highest wind + highest solar)?**
30. **What is the probability of `wind_cap_fac` staying below 15% for more than 24 consecutive hours?**

---

## IV. Zonal Basis & Constraints

*Identifying geographic divergence in the grid.*

31. **What is the difference between North Zone Load and West Zone Load in the P99 scenario?**
32. **Identify hours where West Zone wind generation is > 80% of total RTO wind generation (Export Constraint Risk).**
33. **What is the probability that Houston Load exceeds 25% of total RTO Load?**
34. **Find paths where South Zone temperature is significantly warmer (>10°C) than North Zone.**
35. **Compare the `wind_cap_fac` in the South vs the West load zones during the P10 wind scenario.**
36. **Which zone shows the highest volatility (Std Dev) in load over the next 30 days?**
37. **What is the probability of the North Zone reaching its all-time winter load peak?**
38. **Identify hours where West Zone Solar and West Zone Wind are both above their P90 values.**
39. **How does the South Zone's GHI correlate with RTO-wide GSI?**
40. **What is the P50 total renewable generation (Wind+Solar) for each individual load zone?**

---

## V. Advanced Planning & Tails

*The "What If" scenarios for long-term positioning.*

41. **What is the probability of `net_demand` exceeding 60,000 MW in March?**
42. **Calculate the "Net Demand Uncertainty": (P95 net_demand - P05 net_demand).**
43. **In the top 10% of GSI paths, what is the average `wind_100m_mps` in the West zone?**
44. **What is the likelihood of a "Low Wind, High Outage" event occurring simultaneously?**
45. **What is the average `gsi` when `temp_2m` is between -2°C and 2°C? (The "Freezing Transition").**
46. **Find the date with the highest "Tail Risk" (The largest gap between P50 and P99 GSI).**
47. **What is the probability that `solar_cap_fac` is 0 during an hour where GSI is > 0.80?**
48. **Calculate the expected "Shortfall" (MW) for paths where GSI >= 0.65.**
49. **How many hours in the next 3 months have a >5% probability of GSI > 0.60?**
50. **Identify the "Volatility Peak": The hour with the highest standard deviation in `net_demand` across all paths.**