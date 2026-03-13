document.addEventListener('DOMContentLoaded', () => {
    const jsonInput = document.getElementById('json-input');
    const templateSelector = document.getElementById('template-selector');
    const btnCompile = document.getElementById('btn-compile');
    const compileStatus = document.getElementById('compile-status');
    const resultsDisplay = document.getElementById('results-display');
    const digitalTwinOverlay = document.getElementById('digital-twin-overlay');
    const closeTwinBtn = document.getElementById('close-twin-btn');
    
    let growthChartInstance = null;
    let growthSimulationsMap = {}; // Maps candidate ID to GrowthSimulation

    // Fetch initial template
    loadTemplate(templateSelector.value);

    templateSelector.addEventListener('change', (e) => {
        loadTemplate(e.target.value);
    });

    closeTwinBtn.addEventListener('click', () => {
        digitalTwinOverlay.classList.add('hidden');
    });

    btnCompile.addEventListener('click', async () => {
        const payloadStr = jsonInput.value;
        try {
            const payload = JSON.parse(payloadStr);
            setLoading(true);
            
            const response = await fetch('/api/compile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Compilation Failed');
            }
            
            const result = await response.json();
            renderResults(result);
            
        } catch (error) {
            compileStatus.textContent = 'ERROR';
            compileStatus.className = 'status-badge danger';
            resultsDisplay.innerHTML = `<div class="empty-state">
                <i class="ri-error-warning-line empty-icon" style="color: var(--danger); opacity: 0.5;"></i>
                <p style="color: var(--danger);">${error.message}</p>
            </div>`;
        } finally {
            setLoading(false);
        }
    });

    async function loadTemplate(name) {
        try {
            const res = await fetch(`/api/templates/${name}`);
            if (res.ok) {
                const data = await res.json();
                jsonInput.value = JSON.stringify(data, null, 2);
            }
        } catch (e) {
            console.error('Failed to load template', e);
        }
    }

    function setLoading(isLoading) {
        btnCompile.disabled = isLoading;
        if (isLoading) {
            btnCompile.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> Compiling...';
            compileStatus.textContent = 'COMPILING';
            compileStatus.className = 'status-badge warning';
            digitalTwinOverlay.classList.add('hidden');
        } else {
            btnCompile.innerHTML = '<i class="ri-play-fill"></i> Compile Mission';
        }
    }

    function renderResults(res) {
        compileStatus.textContent = res.allowed ? 'VERIFIED' : 'BLOCKED';
        compileStatus.className = `status-badge ${res.allowed ? 'success' : 'danger'}`;
        
        let html = `
            <div style="margin-bottom: 1rem; border-bottom: 1px solid var(--glass-border); padding-bottom: 1rem;">
                <h3 style="color: white; margin-bottom: 0.5rem;">Mission: ${res.mission.name}</h3>
                <div class="card-metrics">
                    <span class="metric-tag"><i class="ri-shield-check-line"></i> Tier: ${res.risk_tier}</span>
                    <span class="metric-tag"><i class="ri-microscope-line"></i> Containment: ${res.recommended_containment}</span>
                    <span class="metric-tag"><i class="ri-alert-line"></i> Risk Score: ${res.risk_score}/10</span>
                </div>
                <ul class="finding-list">
                    ${res.findings.map(f => `<li>${f}</li>`).join('')}
                </ul>
            </div>
        `;

        if (res.containment_plan && res.containment_plan.active_strategies.length > 0) {
            html += `
                <div style="margin-bottom: 1.5rem;">
                    <h4 style="color: var(--warning); margin-bottom: 0.5rem;"><i class="ri-lock-2-line"></i> Active Biocontainment Plan</h4>
                    <div class="metric-tag" style="background: rgba(245, 158, 11, 0.1); border-color: rgba(245, 158, 11, 0.3);">
                        Strategies: ${res.containment_plan.active_strategies.join(', ')}
                    </div>
                </div>
            `;
        }

        growthSimulationsMap = {};

        if (!res.candidates || res.candidates.length === 0) {
            html += `<p style="color: var(--danger);">No candidates generated (Mission Blocked).</p>`;
        } else {
            html += `<h3 style="color: white; margin-bottom: 1rem;">Candidate Architectures</h3>`;
            html += `<div style="display: flex; flex-direction: column; gap: 1rem;">`;
            
            res.candidates.forEach((c) => {
                if (c.growth_simulation) {
                    growthSimulationsMap[c.id] = c.growth_simulation;
                }
                
                let metricsHtml = '';
                if (c.tea) {
                    metricsHtml += `<span class="metric-tag" title="CAPEX"><i class="ri-money-dollar-circle-line"></i> $${(c.tea.estimated_capex_usd_k/1000).toFixed(1)}M</span>`;
                    metricsHtml += `<span class="metric-tag" title="OPEX"><i class="ri-exchange-dollar-line"></i> $${(c.tea.estimated_opex_usd_k_yr/1000).toFixed(1)}M/yr</span>`;
                    metricsHtml += `<span class="metric-tag" title="Carbon Footprint"><i class="ri-leaf-line"></i> ${c.tea.carbon_footprint_kg_co2_kg_prod.toFixed(1)} kgCO2</span>`;
                }
                if (c.flux) {
                    metricsHtml += `<span class="metric-tag" title="Theoretical Yield Efficiency"><i class="ri-flask-line"></i> ${(c.flux.theoretical_yield*100).toFixed(1)}% Yield</span>`;
                }
                if (c.stability_score !== null) {
                    let stabColor = c.stability_score > 7 ? 'var(--success)' : (c.stability_score > 4 ? 'var(--warning)' : 'var(--danger)');
                    metricsHtml += `<span class="metric-tag" title="Proteostasis Stability" style="border-color: ${stabColor}; color: ${stabColor}"><i class="ri-heart-pulse-line"></i> Stability: ${c.stability_score.toFixed(1)}/10</span>`;
                }
                if (c.evolutionary_risk_score !== null) {
                    let evaColor = c.evolutionary_risk_score < 4 ? 'var(--success)' : (c.evolutionary_risk_score < 7 ? 'var(--warning)' : 'var(--danger)');
                    metricsHtml += `<span class="metric-tag" title="Evolutionary Escape Risk" style="border-color: ${evaColor}; color: ${evaColor}"><i class="ri-seedling-line"></i> Eco-Risk: ${c.evolutionary_risk_score.toFixed(1)}/10</span>`;
                }
                if (c.consortium_stability_index !== null && c.archetype.toLowerCase().includes('consortium')) {
                    metricsHtml += `<span class="metric-tag" title="Consortium Stability Index" style="border-color: var(--accent); color: var(--accent)"><i class="ri-team-line"></i> Symbiosis: ${c.consortium_stability_index.toFixed(1)}/10</span>`;
                }
                if (c.xenobiology_score !== null && c.xenobiology_score > 5.0) {
                    metricsHtml += `<span class="metric-tag" title="Xenobiology Level" style="border-color: #9d4edd; color: #9d4edd"><i class="ri-aliens-line"></i> Xeno-Safety: ${c.xenobiology_score.toFixed(1)}/10</span>`;
                }
                if (c.epigenetic_tunability_score !== null && c.epigenetic_tunability_score > 5.0) {
                    metricsHtml += `<span class="metric-tag" title="Epigenetic Flexibility" style="border-color: #ff9f1c; color: #ff9f1c"><i class="ri-equalizer-line"></i> Epi-Tuning: ${c.epigenetic_tunability_score.toFixed(1)}/10</span>`;
                }
                if (c.plm_fitness_score !== null && c.plm_fitness_score !== undefined) {
                    const plmColor = c.plm_fitness_score >= 7.0 ? '#06d6a0' : (c.plm_fitness_score >= 4.0 ? '#ffd166' : '#ef476f');
                    metricsHtml += `<span class="metric-tag" title="PLM Fitness Landscape" style="border-color: ${plmColor}; color: ${plmColor}"><i class="ri-dna-line"></i> PLM Fitness: ${c.plm_fitness_score.toFixed(1)}/10</span>`;
                }
                if (c.circuit_reliability_score !== null && c.circuit_reliability_score !== undefined) {
                    metricsHtml += `<span class="metric-tag" title="Genetic Circuit Reliability" style="border-color: #118ab2; color: #118ab2"><i class="ri-git-merge-line"></i> Circuit: ${c.circuit_reliability_score.toFixed(1)}/10</span>`;
                }
                if (c.codon_score !== null && c.codon_score !== undefined) {
                    const codonColor = c.codon_score >= 7.0 ? '#2ec4b6' : (c.codon_score >= 4.0 ? '#e0a458' : '#e63946');
                    metricsHtml += `<span class="metric-tag" title="Codon Adaptation" style="border-color: ${codonColor}; color: ${codonColor}"><i class="ri-code-s-slash-line"></i> Codons: ${c.codon_score.toFixed(1)}/10</span>`;
                }
                if (c.crispr_diagnostics_score !== null && c.crispr_diagnostics_score > 0) {
                    metricsHtml += `<span class="metric-tag" title="CRISPR Diagnostics" style="border-color: #e56b6f; color: #e56b6f"><i class="ri-microscope-line"></i> Dx: ${c.crispr_diagnostics_score.toFixed(1)}/10</span>`;
                }
                if (c.growth_simulation) {
                    metricsHtml += `<button class="glass-btn primary btn-sim" data-id="${c.id}" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;">
                        <i class="ri-line-chart-line"></i> View ODE Twin
                    </button>`;
                }

                html += `
                    <div class="result-card">
                        <div class="card-title">
                            ${c.title}
                            <span style="font-size: 0.8rem; font-weight: normal; color: var(--text-muted);">${c.archetype}</span>
                        </div>
                        <div class="card-metrics">${metricsHtml}</div>
                        <p style="font-size: 0.9rem; margin-bottom: 0.5rem; line-height: 1.4;">${c.summary}</p>
                        <div class="metric-tag" style="margin-bottom: 0.5rem;">Modules: ${c.modules.join(', ')}</div>
                `;
                
                if (c.dna_sequence) {
                    let seqPreview = c.dna_sequence.length > 200 ? c.dna_sequence.substring(0, 200) + "..." : c.dna_sequence;
                    html += `
                        <div class="sequence-preview">
                            <div style="color: white; margin-bottom: 4px;">// Proxy DNA Sequence [${c.dna_sequence.length} bp]</div>
                            ${seqPreview}
                        </div>
                    `;
                }
                if (c.stability_findings && c.stability_findings.length > 0) {
                    html += `
                        <div style="margin-top: 0.5rem; font-size: 0.8rem; border-left: 2px solid var(--accent); padding-left: 0.5rem; opacity: 0.8;">
                            <div style="font-weight: bold; margin-bottom: 2px;">Stability Analysis:</div>
                            ${c.stability_findings.map(f => `<div>• ${f}</div>`).join('')}
                        </div>
                    `;
                }
                if (c.genetic_lock_in_strategies && c.genetic_lock_in_strategies.length > 0) {
                    html += `
                        <div style="margin-top: 0.5rem; font-size: 0.8rem; border-left: 2px solid var(--warning); padding-left: 0.5rem; opacity: 0.8;">
                            <div style="font-weight: bold; margin-bottom: 2px; color: var(--warning);">Evolutionary Safeguards:</div>
                            ${c.genetic_lock_in_strategies.map(s => `<div>• ${s}</div>`).join('')}
                        </div>
                    `;
                }
                if (c.consortium_interactions && c.consortium_interactions.length > 0 && c.archetype.toLowerCase().includes('consortium')) {
                    html += `
                        <div style="margin-top: 0.5rem; font-size: 0.8rem; border-left: 2px solid var(--accent); padding-left: 0.5rem; opacity: 0.8;">
                            <div style="font-weight: bold; margin-bottom: 2px; color: var(--accent);">Symbiotic Dynamics:</div>
                            ${c.consortium_interactions.map(i => `<div>• ${i}</div>`).join('')}
                        </div>
                    `;
                }
                if (c.xenobiology_features && c.xenobiology_features.length > 0 && c.xenobiology_score > 5.0) {
                    html += `
                        <div style="margin-top: 0.5rem; font-size: 0.8rem; border-left: 2px solid #9d4edd; padding-left: 0.5rem; opacity: 0.8;">
                            <div style="font-weight: bold; margin-bottom: 2px; color: #9d4edd;">Xeno-Architectures:</div>
                            ${c.xenobiology_features.map(x => `<div>• ${x}</div>`).join('')}
                        </div>
                    `;
                }
                if (c.epigenetic_marks && c.epigenetic_marks.length > 0 && c.epigenetic_tunability_score > 5.0) {
                    html += `
                        <div style="margin-top: 0.5rem; font-size: 0.8rem; border-left: 2px solid #ff9f1c; padding-left: 0.5rem; opacity: 0.8;">
                            <div style="font-weight: bold; margin-bottom: 2px; color: #ff9f1c;">Epigenetic Programming:</div>
                            ${c.epigenetic_marks.map(e => `<div>• ${e}</div>`).join('')}
                        </div>
                    `;
                }
                if (c.plm_fitness_findings && c.plm_fitness_findings.length > 0) {
                    html += `
                        <div style="margin-top: 0.5rem; font-size: 0.8rem; border-left: 2px solid #06d6a0; padding-left: 0.5rem; opacity: 0.8;">
                            <div style="font-weight: bold; margin-bottom: 2px; color: #06d6a0;">PLM Fitness Landscape:</div>
                            ${c.plm_fitness_findings.map(f => `<div>• ${f}</div>`).join('')}
                        </div>
                    `;
                }
                if (c.circuit_findings && c.circuit_findings.length > 0) {
                    html += `
                        <div style="margin-top: 0.5rem; font-size: 0.8rem; border-left: 2px solid #118ab2; padding-left: 0.5rem; opacity: 0.8;">
                            <div style="font-weight: bold; margin-bottom: 2px; color: #118ab2;">Genetic Circuit (Cello-style):</div>
                            ${c.circuit_findings.map(f => `<div>• ${f}</div>`).join('')}
                        </div>
                    `;
                }
                if (c.codon_findings && c.codon_findings.length > 0) {
                    html += `
                        <div style="margin-top: 0.5rem; font-size: 0.8rem; border-left: 2px solid #2ec4b6; padding-left: 0.5rem; opacity: 0.8;">
                            <div style="font-weight: bold; margin-bottom: 2px; color: #2ec4b6;">Codon Optimization:</div>
                            ${c.codon_findings.map(f => `<div>• ${f}</div>`).join('')}
                        </div>
                    `;
                }
                if (c.crispr_diagnostics_assays && c.crispr_diagnostics_assays.length > 0) {
                    html += `
                        <div style="margin-top: 0.5rem; font-size: 0.8rem; border-left: 2px solid #e56b6f; padding-left: 0.5rem; opacity: 0.8;">
                            <div style="font-weight: bold; margin-bottom: 2px; color: #e56b6f;">CRISPR Diagnostics (SHERLOCK/DETECTR):</div>
                            ${c.crispr_diagnostics_assays.map(a => `<div>• [${a.assay}] ${a.target} (${a.sensitivity})</div>`).join('')}
                        </div>
                    `;
                }
                html += `</div>`;
            });
            html += `</div>`;
        }

        resultsDisplay.innerHTML = html;
        
        // Add listeners to Twin buttons
        document.querySelectorAll('.btn-sim').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.currentTarget.getAttribute('data-id');
                showDigitalTwin(id);
            });
        });
    }

    function showDigitalTwin(candidateId) {
        const sim = growthSimulationsMap[candidateId];
        if (!sim) return;
        
        digitalTwinOverlay.classList.remove('hidden');
        
        const ctx = document.getElementById('growthChart').getContext('2d');
        
        if (growthChartInstance) {
            growthChartInstance.destroy();
        }
        
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = 'Outfit';
        
        growthChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sim.time_points_h,
                datasets: [
                    {
                        label: 'Biomass (OD600)',
                        data: sim.biomass_od600,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        yAxisID: 'y',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0
                    },
                    {
                        label: 'Product Titer (g/L)',
                        data: sim.product_titer_gl,
                        borderColor: '#10b981',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        yAxisID: 'y1',
                        tension: 0.4,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        title: { display: true, text: 'Time (Hours)' }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        title: { display: true, text: 'OD600' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        title: { display: true, text: 'Titer (g/L)' }
                    }
                }
            }
        });
    }
});
