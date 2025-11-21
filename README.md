# CIPHER: Counterfeit Image Pattern High-level Examination via Representation for GAN and Diffusion Discriminator Learning
![Architecture](05_Figure/architecture.jpg)

## 초록

The rapid progress of generative adversarial networks (GANs) and diffusion models has enabled the creation of synthetic faces that are increasingly difficult to distinguish from real images. This progress, however, has also amplified the risks of misinformation, fraud, and identity abuse, underscoring the urgent need for detectors that remain robust across diverse generative models. In this work, we introduce Counterfeit Image Pattern High-level Examination via Representation(CIPHER), a deepfake detection framework that systematically reuses and fine-tunes discriminators originally trained for image generation. By extracting scale-adaptive features from ProGAN discriminators and temporal-consistency features from diffusion models, CIPHER captures generation-agnostic artifacts that conventional detectors often overlook. Through extensive experiments across nine state-of-the-art generative models, CIPHER demonstrates superior cross-model detection performance, achieving up to 74.33% F1-score and outperforming existing ViT-based detectors by over 30% in F1-score on average. Notably, our approach maintains robust performance on challenging datasets where baseline methods fail, with up to 88% F1-score on CIFAKE compared to near-zero performance from conventional detectors. These results validate the effectiveness of discriminator reuse and cross-model fine-tuning, establishing CIPHER as a promising approach toward building more generalizable and robust deepfake detection systems in an era of rapidly evolving generative technologies.

### 본 연구는 ICCE-Asia 2025에 채택되었습니다.

본 저장소에서는 연구를 위해 CIPHER에서 사용한 공개된 학습 데이터셋, 실험 코드를 제공합니다.

---

## 프로젝트 소개

이 프로젝트는 2025 제 4회 OUTTA AI 부트캠프 딥러닝반 Advanced의 최종 팀 프로젝트를 위한 스켈레톤 코드입니다.<br>
<br>
이 프로젝트는 이미지를 생성하고 가짜(Deep fake) 이미지를 탐지하는 task입니다.<br>
<br>
이번 프로젝트에서는 ProGAN과 DDPM/DDIM을 이용하여 높은 품질의 가짜 이미지를 생성하고 해당 이미지를 포함해 다양한 데이터셋에서의 딥페이크 탐지 모델을 구현하는 것으로 목표로 합니다.<br>
<br>
이 프로젝트에 대한 자세한 가이드라인 및 평가 기준은 업로드되어 있는 '2025_final_project_guideline.pdf'를 참고하시길 바랍니다.<br>
<br>
이 프로젝트는 Google Colab 환경에서 시행되는 것을 기본으로 하여 제작되었습니다.<br>
<br>

---

## Dataset
![Dataset](05_Figure/dataset.jpg)
데이터셋은 다음의 [링크](https://drive.google.com/drive/folders/1CLorHX2LxSPdwZqsNw2F4QbSkmnVEkJM?usp=sharing)에서 다운로드 받을 수 있습니다.<br>
<br>
데이터셋은 [CelebA-HQ](https://github.com/tkarras/progressive_growing_of_gans)와 [FFHQ](https://github.com/NVlabs/ffhq-dataset)를 활용하였습니다.<br>

---

## 성능 비교
**Fig.1 Performance Comparison: Accuracy (%) and F1-score (%) across Multiple Datasets**
![Tab 1](05_Figure/tab1.png)

**Fig.2 Comparison of Deepfake Detection Models**
<table>
  <thead>
    <tr>
      <th>모델 이름</th>
      <th>아키텍처</th>
      <th>정확도</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><a href="https://huggingface.co/dima806/deepfake_vs_real_image_detection">dima806/deepfake_vs_real</a></td>
      <td>ViT-base</td>
      <td>99.27%</td>
    </tr>
    <tr>
      <td><a href="https://huggingface.co/Wvolf/ViT_Deepfake_Detection">Wvolf/ViT_Deepfake</a></td>
      <td>ViT</td>
      <td>98.70%</td>
    </tr>
    <tr>
      <td><a href="https://github.com/YZY-stack/DF40">DF40 XceptionNet</a> </td>
      <td>XceptionNet</td>
      <td>98.84%</td>
    </tr>
    <tr>
      <td><a href="https://huggingface.co/strangerguardhf/vit_deepfake_detection">strangerguardhf/vit_deepfake</a></td>
      <td>ViT-base</td>
      <td>95.16%</td>
    </tr>
    <tr>
      <td><a href="https://huggingface.co/prithivMLmods/open-deepfake-detection">prithivMLmods/open-deepfake</a></td>
      <td>SigLIP-2</td>
      <td>94.44%</td>
    </tr>
    <tr>
      <td><a href="https://huggingface.co/prithivMLmods/deepfake-detector-model-v1">prithivMLmods/Deep-Fake</a></td>
      <td>SigLIP</td>
      <td>94.44%</td>
    </tr>
  </tbody>
</table>

---

## 참고 문헌

이 저장소는 [DDPM](https://github.com/hojonathanho/diffusion), [DDIM](https://github.com/ermongroup/ddim) 및 [ProGAN](https://github.com/tkarras/progressive_growing_of_gan)을 기반으로 구현되었습니다.

---

## 공지
본 프로젝트를 활용하실 경우, 반드시 OUTTA의 출처를 남겨주시길 바랍니다. OUTTA의 허가 없이 함부로 자료를 무단 배포하는 것을 엄격히 금합니다.
