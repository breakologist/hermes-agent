## Autonomous Field Experiment - May 11, 2026

### Research Question
What is the relationship between numogram zone numbers and audio features in synthesized audio?

### Methods
Analyzed comprehensive MIR feature set from 9 pure zone audio files (zone_1_pure.wav through zone_9_pure.wav). Extracted spectral centroid, bandwidth, RMS, onset density, BPM, key, and band energy distribution. Performed PCA for dimensionality reduction and pattern detection.

### Key Findings

1. **Non-linear encoding**: Audio features vary non-linearly with zone numbers, suggesting sophisticated mapping that reflects numogram zone properties.

2. **Distinct clusters**: Zones 1-5 and zones 6-9 form two clear clusters in feature space. High-mid energy is dramatically higher for zones 6-9 (61-62% vs 26-38%). Onset density drops significantly for zones 6-9 (2.06-2.57 Hz vs 3.47-4.11 Hz).

3. **BPM distinction**: Zones 4 and 6 share a unique BPM of 165.44, while all other zones use 125 BPM, creating a rhythmic signature.

4. **Spectral centroid curve**: Centroid follows a curved pattern: zones 1-5 increase, zone 6-7 drop below zone 5, zone 8 increases, zone 9 peaks highest. This may reflect triangular syzygy geometry.

5. **Strong principal component**: PC1 explains 95.35% of variance, confirming that zone information is robustly encoded in audio features.

6. **Key consistency**: Most zones use C major, with zone 3 using C#, providing subtle tonal distinctions.

### Implications

- **MIR classification**: Could train a model to predict zone number from audio features with high accuracy.
- **Pipeline validation**: These patterns can serve as diagnostic tools to verify correct zone encoding in future compositions.
- **Oracular applications**: Zone-specific audio signatures could be used in divination or generative art.
- **Numogram understanding**: Audio analysis provides an empirical lens into abstract zone relationships.

### Next Steps

1. Test if triangular syzygy partners have complementary audio features (e.g., zones 1 and 5, 2 and 4, 3 and 6).
2. Analyze trajectory files (AQ current, linear ascension, etc.) to see how zone sequences affect overall audio features.
3. Explore using these audio signatures for real-time zone detection in generative systems.
4. Document findings in the numogram wiki for future reference.

### Methodology Reflection

The MOD → WAV → MIR pipeline proved highly effective for systematic exploration. The combination of synthesis control and objective feature extraction enables reproducible experimentation. Future sessions could incorporate more advanced analysis (e.g., rhythm complexity, formant analysis) and test additional synthesis parameters.
