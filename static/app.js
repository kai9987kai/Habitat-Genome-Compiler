document.addEventListener("DOMContentLoaded", () => {
    const dom = {
        jsonInput: document.getElementById("json-input"),
        btnCompile: document.getElementById("btn-compile"),
        btnGenerate: document.getElementById("btn-generate"),
        btnSyncBuilder: document.getElementById("btn-sync-builder"),
        compileStatus: document.getElementById("compile-status"),
        resultsDisplay: document.getElementById("results-display"),
        presetGallery: document.getElementById("preset-gallery"),
        researchInsights: document.getElementById("research-insights"),
        builderPanel: document.getElementById("builder-panel"),
        jsonPanel: document.getElementById("json-panel"),
        modeBuilder: document.getElementById("mode-builder"),
        modeJson: document.getElementById("mode-json"),
        digitalTwinOverlay: document.getElementById("digital-twin-overlay"),
        closeTwinBtn: document.getElementById("close-twin-btn"),
        growthChart: document.getElementById("growthChart"),
    };

    const builderFields = {
        name: document.getElementById("builder-name"),
        domain: document.getElementById("builder-domain"),
        deployment_context: document.getElementById("builder-deployment"),
        architecture_preference: document.getElementById("builder-architecture"),
        problem_focus: document.getElementById("builder-focus"),
        safety_profile: document.getElementById("builder-safety"),
        environment_name: document.getElementById("builder-env-name"),
        temperature_min_c: document.getElementById("builder-temp-min"),
        temperature_max_c: document.getElementById("builder-temp-max"),
        ph_min: document.getElementById("builder-ph-min"),
        ph_max: document.getElementById("builder-ph-max"),
        radiation_level: document.getElementById("builder-radiation"),
        salinity_ppt: document.getElementById("builder-salinity"),
        gravity_g: document.getElementById("builder-gravity"),
        atmosphere: document.getElementById("builder-atmosphere"),
        nutrients: document.getElementById("builder-nutrients"),
        stressors: document.getElementById("builder-stressors"),
        primary_objective_title: document.getElementById("builder-primary-title"),
        primary_objective_metric: document.getElementById("builder-primary-metric"),
        primary_objective_target: document.getElementById("builder-primary-target"),
        secondary_objective_title: document.getElementById("builder-secondary-title"),
        secondary_objective_metric: document.getElementById("builder-secondary-metric"),
        secondary_objective_target: document.getElementById("builder-secondary-target"),
        custom_constraints: document.getElementById("builder-constraints"),
    };

    const state = {
        activeMode: "builder",
        templates: [],
        activeTemplateId: null,
        growthSimulations: {},
        growthChartInstance: null,
        lastGeneratedNotes: [],
    };

    init();

    async function init() {
        bindEvents();
        await loadTemplates();
    }

    function bindEvents() {
        dom.modeBuilder.addEventListener("click", () => setMode("builder"));
        dom.modeJson.addEventListener("click", () => setMode("json"));
        dom.btnGenerate.addEventListener("click", () => generateMissionSpec());
        dom.btnCompile.addEventListener("click", () => compileMission());
        dom.btnSyncBuilder.addEventListener("click", syncBuilderFromJson);
        dom.closeTwinBtn.addEventListener("click", () => {
            dom.digitalTwinOverlay.classList.add("hidden");
        });
    }

    function setMode(mode) {
        state.activeMode = mode;
        dom.builderPanel.classList.toggle("hidden", mode !== "builder");
        dom.jsonPanel.classList.toggle("hidden", mode !== "json");
        dom.modeBuilder.classList.toggle("is-active", mode === "builder");
        dom.modeJson.classList.toggle("is-active", mode === "json");
    }

    async function loadTemplates() {
        try {
            const response = await fetch("/api/templates");
            if (!response.ok) {
                throw new Error("Failed to load preset library");
            }
            const payload = await response.json();
            state.templates = payload.templates || [];
            renderPresetGallery();
            if (state.templates.length > 0) {
                await loadTemplate(state.templates[0].id);
            }
        } catch (error) {
            dom.presetGallery.innerHTML = `<div class="preset-card"><strong>Preset loading failed.</strong><p>${escapeHtml(error.message)}</p></div>`;
        }
    }

    function renderPresetGallery() {
        dom.presetGallery.innerHTML = state.templates.map((template) => `
            <button class="preset-card ${state.activeTemplateId === template.id ? "active" : ""} ${template.status === "blocked-demo" ? "blocked-demo" : ""}" data-template-id="${escapeHtml(template.id)}">
                <span class="preset-domain">${escapeHtml(template.domain)}</span>
                <h4>${escapeHtml(template.name)}</h4>
                <p>${escapeHtml(template.summary)}</p>
                <div class="preset-tags">
                    ${template.status === "blocked-demo" ? "<span>refusal demo</span>" : ""}
                    ${(template.stressors || []).slice(0, 3).map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
                </div>
            </button>
        `).join("");

        dom.presetGallery.querySelectorAll("[data-template-id]").forEach((button) => {
            button.addEventListener("click", async () => {
                await loadTemplate(button.getAttribute("data-template-id"));
            });
        });
    }

    async function loadTemplate(templateId) {
        const response = await fetch(`/api/templates/${templateId}`);
        if (!response.ok) {
            throw new Error("Template not found");
        }
        const mission = await response.json();
        state.activeTemplateId = templateId;
        dom.jsonInput.value = JSON.stringify(mission, null, 2);
        prefillBuilderFromMission(mission);
        renderPresetGallery();
        renderResearchInsights([], "Preset loaded. Generate a fresh spec to see paper-guided builder rules.");
    }

    function prefillBuilderFromMission(mission) {
        const environment = mission.environment || {};
        const objectives = mission.objectives || [];
        const primary = objectives[0] || {};
        const secondary = objectives[1] || {};

        builderFields.name.value = mission.name || "";
        builderFields.domain.value = mission.domain || "industrial-remediation";
        builderFields.deployment_context.value = mission.deployment_context || "";
        builderFields.problem_focus.value = mission.summary || "";
        builderFields.safety_profile.value = inferSafetyProfile(mission);
        builderFields.architecture_preference.value = inferArchitecturePreference(mission);
        builderFields.environment_name.value = environment.name || "";
        builderFields.temperature_min_c.value = Array.isArray(environment.temperature_range_c) ? environment.temperature_range_c[0] : 10;
        builderFields.temperature_max_c.value = Array.isArray(environment.temperature_range_c) ? environment.temperature_range_c[1] : 32;
        builderFields.ph_min.value = Array.isArray(environment.ph_range) ? environment.ph_range[0] : 6.5;
        builderFields.ph_max.value = Array.isArray(environment.ph_range) ? environment.ph_range[1] : 8.0;
        builderFields.radiation_level.value = environment.radiation_level ?? 1.0;
        builderFields.salinity_ppt.value = environment.salinity_ppt ?? 10.0;
        builderFields.gravity_g.value = environment.gravity_g ?? 1.0;
        builderFields.atmosphere.value = (environment.atmosphere || []).join(", ");
        builderFields.nutrients.value = (environment.nutrients || []).join(", ");
        builderFields.stressors.value = (environment.stressors || []).join(", ");
        builderFields.primary_objective_title.value = primary.title || "";
        builderFields.primary_objective_metric.value = primary.metric || "";
        builderFields.primary_objective_target.value = primary.target || "";
        builderFields.secondary_objective_title.value = secondary.title || "";
        builderFields.secondary_objective_metric.value = secondary.metric || "";
        builderFields.secondary_objective_target.value = secondary.target || "";
        builderFields.custom_constraints.value = (mission.biosafety_constraints || []).join("\n");
    }

    function inferSafetyProfile(mission) {
        const constraints = (mission.biosafety_constraints || []).join(" ").toLowerCase();
        if (constraints.includes("layered biocontainment") || constraints.includes("auxotrophy")) {
            return "contained-field-pilot";
        }
        if (constraints.includes("closed loop")) {
            return "closed-loop-pilot";
        }
        return "simulation-only";
    }

    function inferArchitecturePreference(mission) {
        const text = `${mission.summary || ""} ${mission.name || ""}`.toLowerCase();
        if (text.includes("consortium")) {
            return "consortium";
        }
        if (text.includes("living-material") || text.includes("biofilm")) {
            return "living-material";
        }
        if (text.includes("hybrid")) {
            return "hybrid-consortium";
        }
        if (text.includes("single chassis")) {
            return "single-chassis";
        }
        return "auto";
    }

    function collectBuilderPayload() {
        return Object.fromEntries(Object.entries(builderFields).map(([key, input]) => [key, input.value]));
    }

    async function generateMissionSpec() {
        dom.btnGenerate.disabled = true;
        dom.btnGenerate.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> Generating...';
        try {
            const response = await fetch("/api/generate-mission", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(collectBuilderPayload()),
            });
            const payload = await response.json();
            if (!response.ok) {
                throw new Error(payload.detail || "Mission generation failed");
            }
            dom.jsonInput.value = JSON.stringify(payload.mission, null, 2);
            state.lastGeneratedNotes = payload.research_notes || [];
            renderResearchInsights(state.lastGeneratedNotes, payload.builder_summary);
            state.activeTemplateId = null;
            renderPresetGallery();
            return payload.mission;
        } catch (error) {
            renderResearchInsights([], error.message, true);
            throw error;
        } finally {
            dom.btnGenerate.disabled = false;
            dom.btnGenerate.innerHTML = '<i class="ri-sparkling-line"></i> Generate Spec';
        }
    }

    function renderResearchInsights(notes, summary, isError = false) {
        if (!notes.length && !summary) {
            dom.researchInsights.innerHTML = `
                <div class="section-header">
                    <h3><i class="ri-flask-line"></i> Research-backed Builder Prompts</h3>
                </div>
                <p class="empty-copy">Generate a mission spec to see the paper-guided objectives and safety rules applied to your builder inputs.</p>
            `;
            return;
        }

        dom.researchInsights.innerHTML = `
            <div class="section-header">
                <h3><i class="ri-flask-line"></i> Research-backed Builder Prompts</h3>
            </div>
            <p class="${isError ? "error-copy" : "section-caption"}">${escapeHtml(summary || "")}</p>
            <div class="insight-list">
                ${notes.map((note) => `
                    <article class="insight-card">
                        <h4>${escapeHtml(note.title)}</h4>
                        <p>${escapeHtml(note.applied_rule)}</p>
                        <a href="${escapeAttribute(note.url)}" target="_blank" rel="noreferrer">Open source</a>
                    </article>
                `).join("")}
            </div>
        `;
    }

    function syncBuilderFromJson() {
        try {
            const mission = JSON.parse(dom.jsonInput.value);
            prefillBuilderFromMission(mission);
            setMode("builder");
            renderResearchInsights([], "Loaded JSON into the builder fields where the schema matches.");
        } catch (error) {
            renderResearchInsights([], `Could not sync builder from JSON: ${error.message}`, true);
        }
    }

    async function compileMission() {
        try {
            if (state.activeMode === "builder" || !dom.jsonInput.value.trim()) {
                await generateMissionSpec();
            }
            const payload = JSON.parse(dom.jsonInput.value);
            setLoading(true);

            const response = await fetch("/api/compile", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.detail || "Compilation failed");
            }

            renderResults(result);
        } catch (error) {
            dom.compileStatus.textContent = "ERROR";
            dom.compileStatus.className = "status-badge danger";
            dom.resultsDisplay.innerHTML = `
                <div class="empty-state">
                    <i class="ri-error-warning-line empty-icon"></i>
                    <p class="error-copy">${escapeHtml(error.message)}</p>
                </div>
            `;
        } finally {
            setLoading(false);
        }
    }

    function setLoading(isLoading) {
        dom.btnCompile.disabled = isLoading;
        if (isLoading) {
            dom.btnCompile.innerHTML = '<i class="ri-loader-4-line ri-spin"></i> Compiling...';
            dom.compileStatus.textContent = "COMPILING";
            dom.compileStatus.className = "status-badge warning";
            dom.digitalTwinOverlay.classList.add("hidden");
        } else {
            dom.btnCompile.innerHTML = '<i class="ri-play-fill"></i> Compile Mission';
        }
    }

    function renderResults(result) {
        dom.compileStatus.textContent = result.allowed ? "VERIFIED" : "BLOCKED";
        dom.compileStatus.className = `status-badge ${result.allowed ? "success" : "danger"}`;
        state.growthSimulations = {};

        let html = "";
        if (result.saved_run) {
            html += `
                <section class="result-banner">
                    <div>
                        <span class="metric-tag"><i class="ri-archive-line"></i> Run ${escapeHtml(result.saved_run.run_id)}</span>
                        <span class="metric-tag"><i class="ri-folder-line"></i> ${escapeHtml(result.saved_run.directory)}</span>
                    </div>
                </section>
            `;
        }

        html += `
            <section class="result-section">
                <h3>Mission: ${escapeHtml(result.mission.name)}</h3>
                <div class="card-metrics">
                    <span class="metric-tag"><i class="ri-shield-check-line"></i> Tier: ${escapeHtml(result.risk_tier)}</span>
                    <span class="metric-tag"><i class="ri-microscope-line"></i> Containment: ${escapeHtml(result.recommended_containment)}</span>
                    <span class="metric-tag"><i class="ri-alert-line"></i> Risk Score: ${escapeHtml(String(result.risk_score))}/10</span>
                </div>
                <ul class="finding-list">
                    ${(result.findings || []).map((finding) => `<li>${escapeHtml(finding)}</li>`).join("")}
                </ul>
            </section>
        `;

        if (result.containment_plan && result.containment_plan.active_strategies?.length) {
            html += `
                <section class="result-section">
                    <h4 class="section-emphasis"><i class="ri-lock-2-line"></i> Active Biocontainment Plan</h4>
                    <div class="metric-tag emphasis-tag">Strategies: ${escapeHtml(result.containment_plan.active_strategies.join(", "))}</div>
                </section>
            `;
        }

        if (!result.candidates || result.candidates.length === 0) {
            html += `<p class="error-copy">No candidates generated because the mission was blocked.</p>`;
        } else {
            html += `<section class="result-section"><h3>Candidate Architectures</h3><div class="candidate-stack">`;
            result.candidates.forEach((candidate) => {
                if (candidate.growth_simulation) {
                    state.growthSimulations[candidate.id] = candidate.growth_simulation;
                }
                html += renderCandidateCard(candidate);
            });
            html += `</div></section>`;
        }

        dom.resultsDisplay.innerHTML = html;

        dom.resultsDisplay.querySelectorAll(".btn-sim").forEach((button) => {
            button.addEventListener("click", () => {
                showDigitalTwin(button.getAttribute("data-id"));
            });
        });
    }

    function renderCandidateCard(candidate) {
        const metrics = [];
        if (candidate.tea) {
            metrics.push(`<span class="metric-tag"><i class="ri-money-dollar-circle-line"></i> $${escapeHtml((candidate.tea.estimated_capex_usd_k / 1000).toFixed(1))}M CAPEX</span>`);
            metrics.push(`<span class="metric-tag"><i class="ri-exchange-dollar-line"></i> $${escapeHtml((candidate.tea.estimated_opex_usd_k_yr / 1000).toFixed(1))}M/yr OPEX</span>`);
        }
        if (candidate.flux) {
            metrics.push(`<span class="metric-tag"><i class="ri-flask-line"></i> ${escapeHtml((candidate.flux.theoretical_yield * 100).toFixed(1))}% yield</span>`);
        }
        if (candidate.stability_score !== null && candidate.stability_score !== undefined) {
            metrics.push(`<span class="metric-tag"><i class="ri-heart-pulse-line"></i> Stability ${escapeHtml(candidate.stability_score.toFixed(1))}/10</span>`);
        }
        if (candidate.evolutionary_risk_score !== null && candidate.evolutionary_risk_score !== undefined) {
            metrics.push(`<span class="metric-tag"><i class="ri-seedling-line"></i> Eco-risk ${escapeHtml(candidate.evolutionary_risk_score.toFixed(1))}/10</span>`);
        }
        if (candidate.plm_fitness_score !== null && candidate.plm_fitness_score !== undefined) {
            metrics.push(`<span class="metric-tag"><i class="ri-dna-line"></i> PLM ${escapeHtml(candidate.plm_fitness_score.toFixed(1))}/10</span>`);
        }
        if (candidate.circuit_reliability_score !== null && candidate.circuit_reliability_score !== undefined) {
            metrics.push(`<span class="metric-tag"><i class="ri-git-merge-line"></i> Circuit ${escapeHtml(candidate.circuit_reliability_score.toFixed(1))}/10</span>`);
        }
        if (candidate.codon_score !== null && candidate.codon_score !== undefined) {
            metrics.push(`<span class="metric-tag"><i class="ri-code-s-slash-line"></i> Codons ${escapeHtml(candidate.codon_score.toFixed(1))}/10</span>`);
        }
        if (candidate.growth_simulation) {
            metrics.push(`<button class="glass-btn primary btn-sim" data-id="${escapeAttribute(candidate.id)}"><i class="ri-line-chart-line"></i> View ODE Twin</button>`);
        }

        const dnaPreview = candidate.dna_sequence
            ? `
                <div class="sequence-preview">
                    <div class="sequence-title">Proxy DNA Sequence [${escapeHtml(String(candidate.dna_sequence.length))} bp]</div>
                    ${escapeHtml(candidate.dna_sequence.slice(0, 220))}${candidate.dna_sequence.length > 220 ? "..." : ""}
                </div>
            `
            : "";

        const callouts = [
            renderCallout("Stability Analysis", candidate.stability_findings, "accent"),
            renderCallout("Evolutionary Safeguards", candidate.genetic_lock_in_strategies, "warning"),
            candidate.archetype.toLowerCase().includes("consortium")
                ? renderCallout("Symbiotic Dynamics", candidate.consortium_interactions, "accent")
                : "",
            candidate.xenobiology_score > 5 ? renderCallout("Xeno-Architectures", candidate.xenobiology_features, "violet") : "",
            candidate.epigenetic_tunability_score > 5 ? renderCallout("Epigenetic Programming", candidate.epigenetic_marks, "amber") : "",
            renderCallout("PLM Fitness Landscape", candidate.plm_fitness_findings, "mint"),
            renderCallout("Genetic Circuit", candidate.circuit_findings, "sky"),
            renderCallout("Codon Optimization", candidate.codon_findings, "mint"),
            renderCallout("CRISPR Diagnostics", (candidate.crispr_diagnostics_assays || []).map((assay) => `[${assay.assay}] ${assay.target} (${assay.sensitivity})`), "rose"),
        ].join("");

        return `
            <article class="result-card">
                <div class="card-title">
                    <span>${escapeHtml(candidate.title)}</span>
                    <span class="card-subtitle">${escapeHtml(candidate.archetype)}</span>
                </div>
                <div class="card-metrics">${metrics.join("")}</div>
                <p class="candidate-summary">${escapeHtml(candidate.summary)}</p>
                <div class="metric-tag">Modules: ${escapeHtml((candidate.modules || []).join(", "))}</div>
                ${dnaPreview}
                ${callouts}
            </article>
        `;
    }

    function renderCallout(title, items, tone) {
        if (!items || !items.length) {
            return "";
        }
        return `
            <div class="callout tone-${tone}">
                <div class="callout-title">${escapeHtml(title)}</div>
                ${items.map((item) => `<div class="callout-line">&bull; ${escapeHtml(item)}</div>`).join("")}
            </div>
        `;
    }

    function showDigitalTwin(candidateId) {
        const simulation = state.growthSimulations[candidateId];
        if (!simulation) {
            return;
        }

        dom.digitalTwinOverlay.classList.remove("hidden");
        const ctx = dom.growthChart.getContext("2d");

        if (state.growthChartInstance) {
            state.growthChartInstance.destroy();
        }

        Chart.defaults.color = "#94a3b8";
        Chart.defaults.font.family = "Outfit";

        state.growthChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: simulation.time_points_h,
                datasets: [
                    {
                        label: "Biomass (OD600)",
                        data: simulation.biomass_od600,
                        borderColor: "#3b82f6",
                        backgroundColor: "rgba(59, 130, 246, 0.1)",
                        borderWidth: 2,
                        yAxisID: "y",
                        fill: true,
                        tension: 0.35,
                        pointRadius: 0,
                    },
                    {
                        label: "Product Titer (g/L)",
                        data: simulation.product_titer_gl,
                        borderColor: "#10b981",
                        borderWidth: 2,
                        borderDash: [6, 5],
                        yAxisID: "y1",
                        tension: 0.35,
                        pointRadius: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: "index",
                    intersect: false,
                },
                scales: {
                    x: {
                        grid: { color: "rgba(255,255,255,0.05)" },
                        title: { display: true, text: "Time (Hours)" },
                    },
                    y: {
                        type: "linear",
                        position: "left",
                        grid: { color: "rgba(255,255,255,0.05)" },
                        title: { display: true, text: "OD600" },
                    },
                    y1: {
                        type: "linear",
                        position: "right",
                        grid: { drawOnChartArea: false },
                        title: { display: true, text: "Titer (g/L)" },
                    },
                },
            },
        });
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function escapeAttribute(value) {
        return escapeHtml(value);
    }
});
