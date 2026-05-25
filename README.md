# AtmoCorrect-Ray: Tomografi Atmosfer Berbasis Persamaan Diferensial Hirose & Lonngren

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Academic-Field](https://img.shields.io/badge/Field-Geophysics%20%2F%20Geodesy-orange)](https://github.com/)

**AtmoCorrect-Ray** adalah perangkat lunak (*computation engine*) berbasis Python yang dirancang untuk mengeliminasi gangguan atau delay sinyal satelit navigasi (GNSS/GPS) akibat refraksi lapisan atmosfer bumi. Proyek ini mentranslasikan konsep fisis penjalaran gelombang kontinu dari buku teks legendaris *Hirose & Lonngren (2003)* menjadi solusi praktis untuk koreksi koordinat ultra-presisi tingkat **sub-sentimeter (0.5 - 3 cm)** pada industri eksplorasi geofisika dan survei penentuan posisi profesional.

---

## 🛰️ Masalah Industri & Latar Belakang

Pada survei lapangan geofisika (seperti pemetaan titik geofon seismik) maupun monitoring deformasi makro lereng tambang (*open pit monitoring*), akurasi koordinat vertikal dan horizontal adalah parameter kritis. 

Namun, sinyal satelit mentah (**L1, L2, L5**) yang menembus atmosfer bumi mengalami efek:
1. **Dispersi Ionosfer:** Hambatan akibat kerapatan muatan elektron bebas (*Total Electron Content* / TEC).
2. **Refraksi Troposfer:** Pembelokan lintasan fisis (*ray-path bending*) akibat ketidakseragaman (*non-homogenitas*) densitas udara, suhu, dan tekanan lokal.

Jika tidak dikoreksi secara dinamis menggunakan pelacakan lintasan melengkung, deviasi posisi laten di lapangan dapat mencapai skala meter.

---

## 🧬 Landasan Teori Saintifik

### 1. Persamaan Eikonal Kontinu
Menggunakan pendekatan gelombang frekuensi tinggi pada medium tidak homogen, fungsi fase gelombang atau permukaan front gelombang ($\psi$) dikaitkan dengan indeks bias spasial ($n$) melalui persamaan:

$$\left| \nabla \psi(x,y,z) \right|^2 = n^2(x,y,z)$$

### 2. Persamaan Diferensial Lintasan Sinar (Hirose & Lonngren, 2003)
Berdasarkan Prinsip Fermat, gelombang akan melengkung secara kontinu ke arah medium yang memiliki indeks bias lebih rapat. Algoritma pelacakan (*ray-tracing*) ini menyelesaikan sistem persamaan diferensial orde dua terhadap panjang busur berkas sinar ($s$):

$$\frac{d}{ds} \left( n \frac{d\mathbf{r}}{ds} \right) = \nabla n$$

Untuk penyelesaian komputasi numerik, persamaan di atas direduksi menjadi persamaan orde satu berpasangan menggunakan vektor posisi $\mathbf{r}$ dan vektor arah satuan $\mathbf{u} = n(d\mathbf{r}/ds)$:

$$\frac{d\mathbf{r}}{ds} = \frac{\mathbf{u}}{n} \quad ; \quad \frac{d\mathbf{u}}{ds} = \nabla n$$

---

## ⚙️ Alur Kerja Algoritma (Workflow)
# Alur Pemrosesan Sinyal AtmoCorrect-Ray (Workflow)

Dokumen ini menjelaskan arsitektur logika dan alur data dari sistem komputasi Kelompok 9, dimulai dari penangkapan sinyal mentah multi-frekuensi dari satelit hingga menghasilkan output koordinat sub-sentimeter yang siap digunakan untuk keperluan eksplorasi geofisika presisi tinggi.

---

## 📊 Diagram Alur Sistem (Mermaid Flowchart)

```mermaid
graph TD
    %% Penerimaan Data Input
    A[Satelit GNSS: Pancaran Sinyal Mentah] -->|Frekuensi L1, L2, L5| B(Antena Base Station / Rover)
    
    %% Tahap 1: Pemrosesan Ionosfer
    B --> C[Tahap 1: Dekomposisi Efek Ionosfer Dispersif]
    C -->|Kombinasi Linier Pembobot| D{Fase Bebas Ionosfer: &Phi;_IF}
    
    %% Tahap 2: Pemodelan Troposfer
    E[Model Empiris Atmosfer Berlapis] -->|Inisialisasi Refraktivitas N| F[Tahap 2: Pembentukan Profil Indeks Bias 3D Awal]
    D --> F
    
    %% Tahap 3: Pelacakan Berkas Sinar
    F --> G[Tahap 3: Pelacakan Lintasan Melengkung Sinar]
    subgraph Hirose & Lonngren Ray-Tracing Engine (RK4)
        G --> H[Reduksi PD Orde 2 ke Orde 1 Berpasangan]
        H --> I[Integrasi Maju dr/ds & du/ds]
    end
    
    %% Tahap 4: Inversi Tomografi
    I -->|Panjang Lintasan Busur nyata S| J[Tahap 4: Penghitungan Slant Delay &Delta;&tau;]
    J --> K[Diskretisasi Ruang Atmosfer ke Grid Voksel 3D]
    K --> L[Inversi Numerik Weighted Least Squares: y = Ax + e]
    
    %% Tahap 5: Output Akhir
    L -->|Pembaruan Model Indeks Bias Konvergen| M[Tahap 5: Reduksi Bias Fase Utama]
    M --> N[Estimator Posisi Akhir: Modul RTK / PPP]
    N -->|Akurasi Tinggi| O[Data Koordinat Terkoreksi: Sub-Sentimeter 0.5 - 3 cm]

    %% Gaya Visual Diagram
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style O fill:#bbf,stroke:#333,stroke-width:2px
    style D fill:#fff,stroke:#333,stroke-width:1px
    style J fill:#fff,stroke:#333,stroke-width:1px



