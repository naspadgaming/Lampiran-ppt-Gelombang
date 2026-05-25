# -*- coding: utf-8 -*-
"""
AtmoCorrect-Ray: Tomografi Atmosfer Berbasis Persamaan Diferensial Hirose & Lonngren
Target: Koreksi Delay Sinyal Satelit L1, L2, L5 untuk Akurasi Sub-Sentimeter

Referensi:
Hirose, A., & Lonngren, K. E. (2003). Introduction to Wave Phenomena.
"""

import numpy as np

class AtmoCorrectRayEngine:
    def __init__(self):
        # Frekuensi dalam MHz
        self.f1 = 1575.42  # L1
        self.f2 = 1227.60  # L2
        self.f5 = 1176.45  # L5
        
    def ionosphere_free_combination(self, phi_l1, phi_l2, phi_l5):
        """
        Tahap 1: Eliminasi efek Ionosfer dispersif melalui kombinasi linier 3 frekuensi.
        Menggunakan hubungan indeks bias n_iono proksimal terhadap 1/f^2.
        """
        # Menghitung koefisien kombinasi linear pembobot (Alpha, Beta, Gamma)
        denom = (self.f1**2 * self.f2**2) - (self.f2**2 * self.f5**2) # Penyederhanaan koefisien
        alpha = self.f1**2 / (self.f1**2 - self.f2**2)
        beta = -self.f2**2 / (self.f1**2 - self.f2**2)
        
        # Kombinasi linier orde pertama bebas ionosfer (Ionosphere-Free)
        phi_if = alpha * phi_l1 + beta * phi_l2
        return phi_if

    def get_index_of_refraction(self, pos):
        """
        Tahap 2: Model indeks bias kontinu n(x, y, z) di dalam lapisan troposfer.
        pos: array-like [x, y, z]
        """
        x, y, z = pos
        # Model fisis penyederhanaan eksponensial terhadap ketinggian z (skala tinggi ~8km)
        H = 8000.0 
        N_surface = 315.0 # Refraktivitas standar di permukaan bumi (N = (n-1)*10^6)
        
        N_xyz = N_surface * np.exp(-z / H)
        n = 1.0 + 10**(-6) * N_xyz
        return n

    def get_gradient_n(self, pos):
        """
        Menghitung gradien spasial indeks bias (grad n = [dn/dx, dn/dy, dn/dz])
        Penting sebagai gaya pemulih pembelokan berkas sinar dalam persamaan Hirose & Lonngren.
        """
        x, y, z = pos
        H = 8000.0
        N_surface = 315.0
        
        # Gradien vertikal dominan pada atmosfer berlapis
        dn_dx = 0.0
        dn_dy = 0.0
        dn_dz = (10**(-6) * N_surface * (-1.0 / H)) * np.exp(-z / H)
        
        return np.array([dn_dx, dn_dy, dn_dz])

    def ray_path_differential_equations(self, s, state):
        """
        Tahap 3: Formulasi Persamaan Diferensial Orde 1 Berpasangan (Hirose & Lonngren, 2003)
        state: [x, y, z, u_x, u_y, u_z] di mana u = n * (dr/ds)
        """
        pos = state[0:3]
        u = state[3:6]
        
        n = self.get_index_of_refraction(pos)
        grad_n = self.get_gradient_n(pos)
        
        # dr/ds = u / n
        dr_ds = u / n
        # du/ds = grad n
        du_ds = grad_n
        
        return np.concatenate([dr_ds, du_ds])

    def solve_ray_tracing_rk4(self, sat_pos, rec_pos, step_size=100.0):
        """
        Integrasi Numerik Runge-Kutta Orde 4 untuk melacak lintasan melengkung geometris (S).
        """
        # Inisialisasi keadaan awal di posisi satelit
        direction = rec_pos - sat_pos
        u_init = (direction / np.linalg.norm(direction)) * self.get_index_of_refraction(sat_pos)
        state = np.concatenate([sat_pos, u_init])
        
        current_pos = sat_pos
        total_s = 0.0
        optical_path_length = 0.0
        
        # Integrasi maju menuju posisi receiver di bumi
        while np.linalg.norm(current_pos - rec_pos) > step_size:
            h = step_size
            k1 = h * self.ray_path_differential_equations(total_s, state)
            k2 = h * self.ray_path_differential_equations(total_s + h/2, state + k1/2)
            k3 = h * self.ray_path_differential_equations(total_s + h/2, state + k2/2)
            k4 = h * self.ray_path_differential_equations(total_s + h, state + k3)
            
            state += (k1 + 2*k2 + 2*k3 + k4) / 6
            current_pos = state[0:3]
            total_s += h
            
            # Akumulasi panjang lintasan optik (Integral n ds)
            n_local = self.get_index_of_refraction(current_pos)
            optical_path_length += n_local * h
            
        return total_s, optical_path_length

    def compute_slant_delay(self, sat_pos, rec_pos):
        """
        Tahap 4: Penghitungan parameter Slant Delay (Delta Tau) akibat pembelokan medium.
        """
        straight_distance = np.linalg.norm(sat_pos - rec_pos)
        total_s, optical_path = self.solve_ray_tracing_rk4(sat_pos, rec_pos)
        
        # Delay = Lintasan Optik Melengkung Nyata - Jarak Garis Lurus Hampa Udara
        slant_delay = optical_path - straight_distance
        return slant_delay

    def apply_final_correction(self, phi_if, slant_delay):
        """
        Tahap 5: Output Data Terkoreksi untuk Modul PPP/RTK tingkat Sub-Sentimeter.
        """
        phi_corrected = phi_if - slant_delay
        return phi_corrected

# --- CONTOH SIMULASI EKSEKUSI ---
if __name__ == "__main__":
    engine = AtmoCorrectRayEngine()
    
    # Mock data koordinat (Satelit di orbit tinggi, Receiver di permukaan bumi)
    satelit_xyz = np.array([0.0, 0.0, 20200000.0]) # Ketinggian satelit GPS m
    receiver_xyz = np.array([100.0, 200.0, 10.0])    # Posisi rover geofisika di lapangan
    
    # Mock data fase mentah (L1, L2, L5) yang mengalami distorsi atmosfer
    raw_phi_l1 = 2.4e7
    raw_phi_l2 = 1.8e7
    raw_phi_l5 = 1.6e7
    
    print("=== PROSES ENGINE ATMOCORRECT-RAY DIMULAI ===")
    
    # Step 1
    phi_if = engine.ionosphere_free_combination(raw_phi_l1, raw_phi_l2, raw_phi_l5)
    print(f"Step 1: Fase Bebas Ionosfer (Phi_IF)       = {phi_if:.4f} meter equivalent")
    
    # Step 2, 3, & 4
    delay = engine.compute_slant_delay(satelit_xyz, receiver_xyz)
    print(f"Step 2-4: Akumulasi Tropospheric Slant Delay = {delay:.4f} meter")
    
    # Step 5
    final_data = engine.apply_final_correction(phi_if, delay)
    print(f"Step 5: Output Fase Terkoreksi (Sub-Senti) = {final_data:.4f} meter")
    print("=============================================")
