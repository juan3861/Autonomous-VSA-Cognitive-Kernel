use std::collections::HashMap;
use std::time::Instant;

/// ============================================================================
/// 1. SUBSTRATO MATEMÁTICO: ESPAÇO HIPERDIMENSIONAL DE 10.240 BITS (1.28 KB)
/// ============================================================================
pub const WORDS: usize = 160;
pub const BITS: usize = WORDS * 64;
pub const EXPECTED_RANDOM_DIST: f64 = (BITS as f64) * 0.5; // 5120.0
pub const STD_DEV_BITS: f64 = 50.59644256269407; // sqrt(10240 * 0.25)

#[derive(Clone, Copy, PartialEq, Eq)]
#[repr(align(32))] // Alinhamento de 32 bytes para vetorização SIMD (AVX2)
pub struct Hypervector(pub [u64; WORDS]);

impl Hypervector {
    pub const fn zero() -> Self {
        Self([0u64; WORDS])
    }

    /// Gera um hipervetor determinístico ortogonal a partir do nome do conceito
    /// usando FNV-1a + SplitMix64 (Zero dependência de crates externos).
    pub fn from_symbol(symbol: &str) -> Self {
        let mut hash: u64 = 0xcbf29ce484222325;
        for byte in symbol.bytes() {
            hash ^= byte as u64;
            hash = hash.wrapping_mul(0x100000001b3);
        }
        Self::from_seed(hash)
    }

    pub fn from_seed(mut state: u64) -> Self {
        let mut words = [0u64; WORDS];
        for w in words.iter_mut() {
            state = state.wrapping_add(0x9e3779b97f4a7c15);
            let mut z = state;
            z = (z ^ (z >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
            z = (z ^ (z >> 27)).wrapping_mul(0x94d049bb133111eb);
            *w = z ^ (z >> 31);
        }
        Self(words)
    }

    /// OPERADOR 1: BINDING (⊗ via XOR)
    #[inline(always)]
    pub fn bind(&self, other: &Self) -> Self {
        let mut out = [0u64; WORDS];
        for i in 0..WORDS {
            out[i] = self.0[i] ^ other.0[i];
        }
        Self(out)
    }

    /// OPERADOR 2: PERMUTAÇÃO REVERSÍVEL (ρ via Rotação de Palavras + Bits)
    #[inline(always)]
    pub fn permute(&self, steps: usize) -> Self {
        let mut out = [0u64; WORDS];
        let word_shift = steps % WORDS;
        let bit_shift = (steps as u32) % 64;
        for i in 0..WORDS {
            out[(i + word_shift) % WORDS] = self.0[i].rotate_left(bit_shift);
        }
        Self(out)
    }

    /// INVERSO DA PERMUTAÇÃO (ρ^-1)
    #[inline(always)]
    pub fn unpermute(&self, steps: usize) -> Self {
        let mut out = [0u64; WORDS];
        let word_shift = steps % WORDS;
        let bit_shift = (steps as u32) % 64;
        for i in 0..WORDS {
            out[i] = self.0[(i + word_shift) % WORDS].rotate_right(bit_shift);
        }
        Self(out)
    }

    /// OPERADOR 3: BUNDLING / SUPERPOSIÇÃO HOLOGRÁFICA (⊕ via Voto Majoritário)
    pub fn bundle(vectors: &[Hypervector]) -> Self {
        if vectors.is_empty() {
            return Self::zero();
        }
        let n = vectors.len();
        let tie_breaker = Self::from_seed(0x517cc1b727220a95 ^ (n as u64));
        let threshold = n / 2;
        let mut out = [0u64; WORDS];

        for word_idx in 0..WORDS {
            let mut result_word = 0u64;
            for bit in 0..64 {
                let mask = 1u64 << bit;
                let mut ones_count = 0usize;
                for v in vectors {
                    if (v.0[word_idx] & mask) != 0 {
                        ones_count += 1;
                    }
                }
                let bit_val = if n % 2 == 0 && ones_count == threshold {
                    (tie_breaker.0[word_idx] & mask) != 0
                } else {
                    ones_count > threshold
                };
                if bit_val {
                    result_word |= mask;
                }
            }
            out[word_idx] = result_word;
        }
        Self(out)
    }

    /// DISTÂNCIA DE HAMMING (Instrução POPCNT de Hardware)
    #[inline(always)]
    pub fn hamming_distance(&self, other: &Self) -> u32 {
        let mut dist = 0u32;
        for i in 0..WORDS {
            dist += (self.0[i] ^ other.0[i]).count_ones();
        }
        dist
    }

    /// RESSONÂNCIA EM SIGMAS (Z-Score Estatístico)
    #[inline(always)]
    pub fn resonance_sigma(&self, other: &Self) -> f64 {
        let dist = self.hamming_distance(other) as f64;
        (EXPECTED_RANDOM_DIST - dist) / STD_DEV_BITS
    }

    /// ENERGIA LIVRE / SURPRESA NORMALIZADA
    #[inline(always)]
    pub fn surprise(&self, other: &Self) -> f64 {
        let dist = self.hamming_distance(other) as f64;
        (dist / EXPECTED_RANDOM_DIST).clamp(0.0, 2.0)
    }

    /// DANO / RUÍDO TÉRMICO
    pub fn inject_noise(&self, flip_ratio: f64, seed: u64) -> Self {
        let mut out = self.0;
        let mut rng = seed ^ 0x2545f4914f6cdd1d;
        let threshold = (flip_ratio.clamp(0.0, 1.0) * (u32::MAX as f64)) as u32;

        for w in out.iter_mut() {
            let mut flip_mask = 0u64;
            for bit in 0..64 {
                rng ^= rng >> 12;
                rng ^= rng << 25;
                rng ^= rng >> 27;
                let rand_u32 = (rng.wrapping_mul(0x2545f4914f6cdd1d) >> 32) as u32;
                if rand_u32 < threshold {
                    flip_mask |= 1u64 << bit;
                }
            }
            *w ^= flip_mask;
        }
        Self(out)
    }
}

/// ============================================================================
/// 2. KERNEL COGNITIVO: MEMÓRIA DE LIMPEZA + INFERÊNCIA ATIVA (GAMMA / THETA)
/// ============================================================================
pub struct CognitiveKernel {
    pub lexicon: HashMap<String, Hypervector>,
    pub role_state: Hypervector,
    pub role_action: Hypervector,
    pub role_outcome: Hypervector,
    pub hippocampus_traces: Vec<Hypervector>,
    pub semantic_cortex: Hypervector,
    pub surprise_threshold: f64,
}

impl CognitiveKernel {
    pub fn new(surprise_threshold: f64) -> Self {
        Self {
            lexicon: HashMap::new(),
            role_state: Hypervector::from_symbol("__ROLE_STATE__"),
            role_action: Hypervector::from_symbol("__ROLE_ACTION__"),
            role_outcome: Hypervector::from_symbol("__ROLE_OUTCOME__"),
            hippocampus_traces: Vec::new(),
            semantic_cortex: Hypervector::zero(),
            surprise_threshold,
        }
    }

    pub fn symbol(&mut self, name: &str) -> Hypervector {
        *self
            .lexicon
            .entry(name.to_string())
            .or_insert_with(|| Hypervector::from_symbol(name))
    }

    pub fn cleanup(&self, noisy_vec: &Hypervector) -> Option<(String, u32, f64)> {
        let mut best_match: Option<(String, u32, f64)> = None;
        for (name, clean_vec) in &self.lexicon {
            let dist = noisy_vec.hamming_distance(clean_vec);
            let sigma = noisy_vec.resonance_sigma(clean_vec);
            if best_match.is_none() || dist < best_match.as_ref().unwrap().1 {
                best_match = Some((name.clone(), dist, sigma));
            }
        }
        best_match
    }

    pub fn predict_outcome(&mut self, state_name: &str, action_name: &str) -> Hypervector {
        let s = self.symbol(state_name);
        let a = self.symbol(action_name);
        let context_key = s.bind(&a);
        self.semantic_cortex.bind(&context_key).unpermute(1)
    }

    pub fn step_active_inference(
        &mut self,
        state_name: &str,
        action_name: &str,
        actual_outcome_name: &str,
    ) {
        let t0 = Instant::now();

        let s = self.symbol(state_name);
        let a = self.symbol(action_name);
        let o_actual = self.symbol(actual_outcome_name);

        let o_predicted = self.predict_outcome(state_name, action_name);

        let free_energy = if self.hippocampus_traces.is_empty() {
            1.0
        } else {
            o_actual.surprise(&o_predicted)
        };

        let decoded_pred = self
            .cleanup(&o_predicted)
            .map(|(name, _, sigma)| format!("{} ({:.1}σ)", name, sigma))
            .unwrap_or_else(|| "N/A".to_string());

        let elapsed_ns = t0.elapsed().as_nanos();

        println!(
            "  [GAMMA {:>5} ns] Contexto: ({} + {}) | Previsto: {:<28} | Real: {}",
            elapsed_ns, state_name, action_name, decoded_pred, actual_outcome_name
        );

        if free_energy > self.surprise_threshold {
            println!(
                "    ⚡ [CHOQUE EPISTÊMICO! Surpresa F = {:.3} > {:.2}] -> Acordando Ciclo THETA...",
                free_energy, self.surprise_threshold
            );

            let causal_trace = s.bind(&a).bind(&o_actual.permute(1));
            self.hippocampus_traces.push(causal_trace);
            self.semantic_cortex = Hypervector::bundle(&self.hippocampus_traces);
            println!(
                "    🧠 [THETA] Regra causal gravada em 1 passo no Hipervetor Cortical (Total de leis no mesmo 1.28 KB: {}).",
                self.hippocampus_traces.len()
            );
        } else {
            println!(
                "    ✅ [HOMEOSTASE F = {:.3}] Predição confirmada! Ação reflexa executada (0% GPU / 0% LLM).",
                free_energy
            );
        }
    }

    pub fn encode_structured_episode(
        &mut self,
        state_name: &str,
        action_name: &str,
        outcome_name: &str,
    ) -> Hypervector {
        let s = self.symbol(state_name);
        let a = self.symbol(action_name);
        let o = self.symbol(outcome_name);

        let bound_s = self.role_state.bind(&s);
        let bound_a = self.role_action.bind(&a);
        let bound_o = self.role_outcome.bind(&o);

        Hypervector::bundle(&[bound_s, bound_a, bound_o])
    }

    pub fn dream_consolidation(&mut self, noisy_day_traces: &[Hypervector]) -> Hypervector {
        Hypervector::bundle(noisy_day_traces)
    }
}

fn main() {
    println!("================================================================================");
    println!("  AETHERMIND VSA KERNEL - 10.240 BITS | ACTIVE INFERENCE & HOLOGRAPHIC MEMORY");
    println!("  Tamanho de cada Pensamento: {} bits ({} bytes / 1.28 KB)", BITS, WORDS * 8);
    println!("================================================================================\n");

    let mut kernel = CognitiveKernel::new(0.82);

    println!(">>> FASE 1: EXPOSIÇÃO AO AMBIENTE (PRIMEIRA VEZ - TABULA RASA)");
    kernel.step_active_inference("VRAM_CRITICA", "ATIVAR_QUANT_Q4", "ESTABILIDADE_OK");
    kernel.step_active_inference("TEMP_CPU_ALTA", "REDUZIR_CLOCK", "RESFRIAMENTO_OK");
    kernel.step_active_inference("REDE_INSTAVEL", "ROTEAR_LOCAL", "LATENCIA_ZERO");
    kernel.step_active_inference("PROMPT_COMPLEXO", "LOOP_LATENTE_4X", "RACIOCINIO_PROFUNDO");

    println!("\n>>> FASE 2: SEGUNDA EXPOSIÇÃO AOS MESMOS EVENTOS (VERIFICANDO PREDIÇÃO ATIVA)");
    kernel.step_active_inference("VRAM_CRITICA", "ATIVAR_QUANT_Q4", "ESTABILIDADE_OK");
    kernel.step_active_inference("TEMP_CPU_ALTA", "REDUZIR_CLOCK", "RESFRIAMENTO_OK");
    kernel.step_active_inference("REDE_INSTAVEL", "ROTEAR_LOCAL", "LATENCIA_ZERO");
    kernel.step_active_inference("PROMPT_COMPLEXO", "LOOP_LATENTE_4X", "RACIOCINIO_PROFUNDO");

    println!("\n>>> FASE 3: GRAFO HOLOGRÁFICO E RESISTÊNCIA A DESTRUIÇÃO DE MEMÓRIA");
    let episode = kernel.encode_structured_episode(
        "VRAM_CRITICA",
        "ATIVAR_QUANT_Q4",
        "ESTABILIDADE_OK",
    );

    let damaged_episode = episode.inject_noise(0.35, 2077);
    let corrupted_bits = episode.hamming_distance(&damaged_episode);
    println!(
        "  • Dano infligido ao Hipervetor: {} de {} bits destruídos ({:.1}% de corrupção)",
        corrupted_bits,
        BITS,
        (corrupted_bits as f64 / BITS as f64) * 100.0
    );

    let t_unpack = Instant::now();
    let query_action_vec = damaged_episode.bind(&kernel.role_action);
    let (recovered_action, dist, sigma) = kernel.cleanup(&query_action_vec).unwrap();
    let unpack_ns = t_unpack.elapsed().as_nanos();

    println!(
        "  • Consulta Algébrica (Episódio_Danificado ⊗ ROLE_ACTION) em {} ns:",
        unpack_ns
    );
    println!(
        "    -> Conceito Recuperado: '{}' | Distância Hamming: {} | Certeza: +{:.2} Sigmas!",
        recovered_action, dist, sigma
    );

    println!("\n>>> FASE 4: RACIOCÍNIO ANALÓGICO DIRETO NO ESPAÇO LATENTE BINÁRIO");
    let role_proc = kernel.symbol("PAPEL_PROCESSADOR");
    let role_mem = kernel.symbol("PAPEL_MEMORIA");

    let cortex = kernel.symbol("CORTEX_PRE_FRONTAL");
    let hipocampo = kernel.symbol("HIPOCAMPO_BIOLOGICO");
    let dory4b = kernel.symbol("DORY_4B_LOOPED");
    let vsa_kernel = kernel.symbol("VSA_10240_KERNEL");

    let bio_brain = Hypervector::bundle(&[role_proc.bind(&cortex), role_mem.bind(&hipocampo)]);
    let cyber_brain = Hypervector::bundle(&[role_proc.bind(&dory4b), role_mem.bind(&vsa_kernel)]);

    let t_analogy = Instant::now();
    let transformation_bridge = bio_brain.bind(&cyber_brain);
    let analogy_result = transformation_bridge.bind(&dory4b);
    let (analog_match, _, analog_sigma) = kernel.cleanup(&analogy_result).unwrap();
    let analogy_ns = t_analogy.elapsed().as_nanos();

    println!(
        "  • Pergunta: 'Se no AetherMind usamos DORY_4B_LOOPED, qual o equivalente no Cérebro Biológico?'"
    );
    println!(
        "  • Cálculo (Bio_Brain ⊗ Cyber_Brain ⊗ DORY_4B_LOOPED) executado em {} ns:",
        analogy_ns
    );
    println!(
        "    -> Dedução Algébrica: '{}' (Ressonância: +{:.2}σ)",
        analog_match, analog_sigma
    );

    println!("\n>>> FASE 5: MODO SONHO (CONSOLIDAÇÃO REM DE TRAÇOS COM RUÍDO TÉRMICO)");
    let hidden_law = kernel
        .symbol("CAUSA_DESCONHECIDA")
        .bind(&kernel.symbol("EFEITO_EMERGENTE"));

    let noisy_observations: Vec<Hypervector> = (1..=7)
        .map(|i| hidden_law.inject_noise(0.40, i * 99991))
        .collect();

    let dream_attractor = kernel.dream_consolidation(&noisy_observations);
    let dream_query = dream_attractor.bind(&kernel.symbol("CAUSA_DESCONHECIDA"));
    let (dream_insight, _, dream_sigma) = kernel.cleanup(&dream_query).unwrap();

    println!(
        "  • 7 memórias diárias severamente corrompidas (40% de ruído cada) fundidas em Fase REM:"
    );
    println!(
        "    -> Lei Oculta Extraída durante o Sonho: CAUSA_DESCONHECIDA => '{}' (+{:.2}σ)",
        dream_insight, dream_sigma
    );
}
