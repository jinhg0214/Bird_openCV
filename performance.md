# Model Performance Comparison

| Model Name | Input Resolution | Precision | Recall | mAP@.50 | mAP@.50-.95 | Inference Time (ms) | CPU Usage (%) | Memory (MB) | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `bird_detect_320.pt` | 320x320 | 0.779 | 0.802 | 0.819 | 0.643 | | | | |
| `bird_detect_416.pt` | 416x416 | 0.873 | 0.750 | 0.826 | 0.627 | | | | |
| `bird_detect_640.pt` | 640x640 | 0.943 | 0.750 | 0.879 | 0.656 | | | | |

---

## 항목 설명

*   **Model Name**: 모델의 파일 이름
*   **Input Resolution**: 모델 학습 및 추론에 사용되는 이미지의 해상도(가로x세로)
*   **Precision (정밀도)**: 모델이 '새'라고 예측한 결과 중, 실제로 '새'인 객체의 비율 (TP / (TP + FP))
*   **Recall (재현율)**: 실제 '새' 객체 중에서 모델이 '새'라고 올바르게 감지한 객체의 비율 (TP / (TP + FN))
*   **mAP@.50**: IoU(Intersection over Union) 임계값을 0.5로 설정했을 때의 mAP(mean Average Precision) 값, 객체 탐지 모델의 전반적인 정확도를 평가하는 일반적인 지표
*   **mAP@.50-.95**: IoU 임계값을 0.5부터 0.95까지 0.05씩 높여가며 측정한 mAP의 평균값, 더 엄격하고 신뢰도 높은 평가지표
*   **Inference Time (ms)**: **(Raspberry Pi에서 측정)** 모델이 이미지 한 장을 분석하고 결과를 내놓기까지 걸리는 시간 (밀리초 단위)
*   **CPU Usage (%)**: **(Raspberry Pi에서 측정)** 모델 추론 시 CPU 사용률
*   **Memory (MB)**: **(Raspberry Pi에서 측정)** 모델 추론 시 사용되는 메모리(RAM)의 양
*   **Notes (비고)**: 각 모델에 대한 추가적인 설명이나 테스트 조건 등