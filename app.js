import { pipeline, cos_sim } from 'https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2';

// Global variables
let extractor = null;
let chart = null;
let currentSurveyData = null; // Store latest survey results

// ============================================
// CORE SSR ALGORITHM (from research paper)
// ============================================

// Initialize the embedding model
async function initializeModel() {
    if (!extractor) {
        try {
            extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
        } catch (error) {
            console.error('Error loading model:', error);
            throw new Error('Failed to load embedding model. Please check your internet connection.');
        }
    }
    return extractor;
}

// Get embedding for a text
async function getEmbedding(text) {
    const model = await initializeModel();
    const output = await model(text, { pooling: 'mean', normalize: true });
    return Array.from(output.data);
}

// Calculate cosine similarity
function cosineSimilarity(vecA, vecB) {
    return cos_sim(vecA, vecB);
}

// SSR Algorithm: Convert single text response to Likert distribution
async function semanticSimilarityRating(response, anchors) {
    const responseEmbedding = await getEmbedding(response);
    const anchorEmbeddings = await Promise.all(
        anchors.map(anchor => getEmbedding(anchor))
    );

    // Calculate cosine similarities
    const similarities = anchorEmbeddings.map(anchorEmb =>
        cosineSimilarity(responseEmbedding, anchorEmb)
    );

    // Apply SSR transformation
    const minSim = Math.min(...similarities);
    const shiftedSims = similarities.map(s => s - minSim);
    const epsilon = 1e-8;
    const regularizedSims = shiftedSims.map(s => s + epsilon);
    const sumSims = regularizedSims.reduce((a, b) => a + b, 0);
    const probabilities = regularizedSims.map(s => s / sumSims);

    return {
        similarities,
        probabilities,
        rawSimilarities: similarities
    };
}

// ============================================
// BATCH PROCESSING (NEW - Paper's methodology)
// ============================================

// Parse responses from textarea (smart detection)
function parseResponses(inputText) {
    if (!inputText || !inputText.trim()) {
        return [];
    }

    // Try to detect if it's JSON array
    try {
        const parsed = JSON.parse(inputText);
        if (Array.isArray(parsed)) {
            return parsed.map(item =>
                typeof item === 'string' ? item : (item.response || item.text || String(item))
            );
        }
    } catch (e) {
        // Not JSON, continue with line-based parsing
    }

    // Split by newlines and filter empties
    return inputText
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);
}

// Analyze batch of responses and aggregate into survey distribution
async function analyzeSurveyBatch(responses, anchors, progressCallback) {
    const individualPMFs = [];

    for (let i = 0; i < responses.length; i++) {
        if (progressCallback) {
            progressCallback(i + 1, responses.length);
        }

        const pmf = await semanticSimilarityRating(responses[i], anchors);
        individualPMFs.push(pmf);
    }

    // Aggregate PMFs (average probabilities across all responses)
    const aggregated = aggregatePMFs(individualPMFs);

    return {
        aggregatedDistribution: aggregated,
        individualPMFs: individualPMFs,
        totalResponses: responses.length
    };
}

// Aggregate multiple PMFs into single distribution
function aggregatePMFs(pmfs) {
    const numResponses = pmfs.length;
    const aggregated = [0, 0, 0, 0, 0];

    for (const pmf of pmfs) {
        for (let i = 0; i < 5; i++) {
            aggregated[i] += pmf.probabilities[i];
        }
    }

    // Average (this creates the survey-level distribution)
    return aggregated.map(p => p / numResponses);
}

// Calculate survey statistics from aggregated distribution
function calculateSurveyStatistics(aggregatedPMF, responseCount) {
    // Mode (most common rating)
    const mode = aggregatedPMF.indexOf(Math.max(...aggregatedPMF)) + 1;

    // Mean (expected value)
    const mean = aggregatedPMF.reduce((sum, prob, idx) => sum + prob * (idx + 1), 0);

    // Standard deviation
    const variance = aggregatedPMF.reduce((sum, prob, idx) => {
        const diff = (idx + 1) - mean;
        return sum + prob * diff * diff;
    }, 0);
    const stdDev = Math.sqrt(variance);

    // Count at each level (convert probabilities to counts)
    const levelCounts = aggregatedPMF.map(prob => Math.round(prob * responseCount));

    return {
        mode,
        mean,
        stdDev,
        levelCounts,
        totalResponses: responseCount
    };
}

// ============================================
// PERSONA GENERATOR (TIER 2)
// ============================================

// Generate balanced demographic profiles
function generatePersonaPrompts(config) {
    const {
        count = 50,
        ageRanges = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'],
        incomeRanges = ['<$25k', '$25-50k', '$50-75k', '$75-100k', '$100k+'],
        genders = { Male: 33, Female: 34, Other: 33 },
        locations = ['Urban', 'Suburban', 'Rural'],
        surveyQuestion = ''
    } = config;

    const prompts = [];

    for (let i = 0; i < count; i++) {
        const profile = createDemographicProfile(ageRanges, incomeRanges, genders, locations);
        const prompt = formatPersonaPrompt(profile, surveyQuestion, i + 1);
        prompts.push(prompt);
    }

    return prompts;
}

// Create single demographic profile with balanced distribution
function createDemographicProfile(ageRanges, incomeRanges, genders, locations) {
    // Random selection from each category
    const age = ageRanges[Math.floor(Math.random() * ageRanges.length)];
    const income = incomeRanges[Math.floor(Math.random() * incomeRanges.length)];
    const location = locations[Math.floor(Math.random() * locations.length)];

    // Gender selection based on percentages
    const genderRandom = Math.random() * 100;
    let cumulativePercent = 0;
    let gender = 'Other';

    for (const [g, percent] of Object.entries(genders)) {
        cumulativePercent += percent;
        if (genderRandom < cumulativePercent) {
            gender = g;
            break;
        }
    }

    return { age, income, gender, location };
}

// Format persona prompt template
function formatPersonaPrompt(profile, surveyQuestion, index) {
    const ageDisplay = profile.age.includes('-') ?
        `${parseInt(profile.age.split('-')[0]) + Math.floor(Math.random() * 5)}-year-old` :
        `${profile.age} years old`;

    const locationDesc = profile.location.toLowerCase();
    const incomeDesc = profile.income;

    return `${index}. You are a ${ageDisplay} ${profile.gender.toLowerCase()} from a ${locationDesc} area with household income of ${incomeDesc}. ${surveyQuestion}`;
}

// Copy prompts to clipboard
async function copyPersonaPromptsToClipboard(prompts) {
    const text = prompts.join('\n\n');
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        console.error('Failed to copy:', err);
        return false;
    }
}

// ============================================
// B2B PERSONA SUPPORT (TIER 2.5)
// ============================================

// Auto-detect delimiter (tab vs comma) for Excel/Word paste support
function detectDelimiter(text) {
    const firstLine = text.split('\n')[0];
    const tabCount = (firstLine.match(/\t/g) || []).length;
    const commaCount = (firstLine.match(/,/g) || []).length;

    // If more tabs than commas, it's TSV (Excel/Word copy-paste)
    return tabCount > commaCount ? '\t' : ',';
}

// Parse B2B persona definitions from pasted table
function parsePersonaDefinitions(text) {
    const delimiter = detectDelimiter(text);
    const lines = text.trim().split('\n');

    if (lines.length < 2) {
        throw new Error('Need header row + at least one persona');
    }

    const header = parseCSVLine(lines[0], delimiter);

    // Flexible column matching - find "role" column (case-insensitive)
    const roleColIdx = header.findIndex(h =>
        /role|persona|title|position|functional.?team/i.test(h)
    );

    if (roleColIdx === -1) {
        throw new Error('Table must have "role", "persona", or "title" column');
    }

    const personas = [];
    for (let i = 1; i < lines.length; i++) {
        const values = parseCSVLine(lines[i], delimiter);
        if (values.length === 0 || !values[roleColIdx]) continue;

        const persona = {};
        header.forEach((col, idx) => {
            // Normalize column names to snake_case
            const key = col.toLowerCase().replace(/[\s\/\(\)]+/g, '_').replace(/_+/g, '_');
            persona[key] = values[idx] || '';
        });
        personas.push(persona);
    }

    return personas;
}

// Generate B2B survey prompts from persona definitions
function generateB2BPrompts(personas, surveyQuestion, totalResponses = 50) {
    const prompts = [];
    const responsesPerPersona = Math.ceil(totalResponses / personas.length);

    personas.forEach((persona, pIdx) => {
        // Extract fields with flexible column name matching
        const role = persona.role || persona.persona || persona.title ||
                     persona.persona_functional_team || `Persona ${pIdx + 1}`;

        const dept = persona.department || persona.team || persona.functional_team || '';

        const resp = persona.responsibilities || persona.role_typical_responsibility ||
                     persona.role___typical_responsibility || '';

        const pain = persona.pain_points || persona.pain_points_challenges ||
                     persona.challenges || persona.pain_points___challenges || '';

        const needs = persona.key_needs || persona.key_needs_objectives ||
                      persona.objectives || persona.key_needs___objectives || '';

        // Generate variations per persona (different seniority, company size)
        for (let v = 0; v < responsesPerPersona; v++) {
            const seniority = ['Junior', 'Mid-Level', 'Senior', 'Lead'][v % 4];
            const companySize = [
                'small (10-50 employees)',
                'medium (100-500 employees)',
                'large (1000-5000 employees)',
                'enterprise (10,000+ employees)'
            ][Math.floor(v / 4) % 4];

            let prompt = `You are a ${seniority} ${role}`;
            if (dept) prompt += ` in the ${dept} department`;
            prompt += ` at a ${companySize} organization.\n\n`;

            if (resp) prompt += `Your key responsibilities include: ${resp}\n\n`;
            if (needs) prompt += `Your main objectives are: ${needs}\n\n`;
            if (pain) prompt += `Challenges you face: ${pain}\n\n`;

            prompt += `${surveyQuestion}\n\nPlease respond naturally based on your professional perspective and experience.`;

            prompts.push({
                index: prompts.length + 1,
                persona: role,
                department: dept,
                seniority: seniority,
                companySize: companySize,
                prompt: prompt.trim()
            });
        }
    });

    return prompts;
}

// ============================================
// CSV PARSER & DEMOGRAPHICS (TIER 3)
// ============================================

// Parse CSV with demographics
function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) {
        throw new Error('CSV must have header row and at least one data row');
    }

    // Parse header
    const header = parseCSVLine(lines[0]);
    const requiredColumns = ['response'];
    const optionalColumns = ['age', 'income', 'gender', 'location'];

    // Validate header
    if (!header.includes('response')) {
        throw new Error('CSV must have a "response" column');
    }

    // Parse data rows
    const responses = [];
    const demographics = [];

    for (let i = 1; i < lines.length; i++) {
        const values = parseCSVLine(lines[i]);
        if (values.length === 0) continue; // Skip empty lines

        const row = {};
        header.forEach((col, idx) => {
            row[col] = values[idx] || '';
        });

        responses.push(row.response);
        demographics.push({
            age: row.age || null,
            income: row.income || null,
            gender: row.gender || null,
            location: row.location || null
        });
    }

    return { responses, demographics, hasDemographics: header.some(h => optionalColumns.includes(h)) };
}

// Parse single CSV line (handles quotes, supports custom delimiter for TSV)
function parseCSVLine(line, delimiter = ',') {
    const result = [];
    let current = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
        const char = line[i];

        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === delimiter && !inQuotes) {
            result.push(current.trim());
            current = '';
        } else {
            current += char;
        }
    }

    result.push(current.trim());
    return result.map(v => v.replace(/^"|"$/g, '')); // Remove surrounding quotes
}

// Validate CSV format
function validateCSVFormat(csvData) {
    if (!csvData.responses || csvData.responses.length === 0) {
        throw new Error('No responses found in CSV');
    }

    if (csvData.responses.some(r => !r || r.trim().length === 0)) {
        throw new Error('CSV contains empty responses');
    }

    return true;
}

// Segment responses by demographic attribute
function segmentByDemographic(responses, demographics, pmfs, segmentKey) {
    const segments = {};

    responses.forEach((response, idx) => {
        const demo = demographics[idx];
        const key = demo[segmentKey] || 'Unknown';

        if (!segments[key]) {
            segments[key] = {
                responses: [],
                pmfs: [],
                count: 0
            };
        }

        segments[key].responses.push(response);
        segments[key].pmfs.push(pmfs[idx]);
        segments[key].count++;
    });

    // Calculate aggregated PMF for each segment
    for (const key in segments) {
        segments[key].aggregatedPMF = aggregatePMFs(segments[key].pmfs);
        segments[key].stats = calculateSurveyStatistics(segments[key].aggregatedPMF, segments[key].count);
    }

    return segments;
}

// Calculate demographic insights
function calculateDemographicInsights(segmentedResults) {
    const insights = [];
    const segments = Object.entries(segmentedResults);

    if (segments.length < 2) return insights;

    // Compare means across segments
    segments.sort((a, b) => b[1].stats.mean - a[1].stats.mean);
    const highest = segments[0];
    const lowest = segments[segments.length - 1];

    const diff = (highest[1].stats.mean - lowest[1].stats.mean).toFixed(2);
    if (Math.abs(diff) > 0.3) {
        insights.push(`${highest[0]} rates ${diff} points higher than ${lowest[0]}`);
    }

    // Check for strong preferences (>60% in top 2 ratings)
    for (const [key, data] of segments) {
        const topTwoPercent = (data.aggregatedPMF[3] + data.aggregatedPMF[4]) * 100;
        if (topTwoPercent > 60) {
            insights.push(`${key}: ${topTwoPercent.toFixed(0)}% show high preference (ratings 4-5)`);
        }
    }

    return insights;
}

// ============================================
// UI UPDATE FUNCTIONS
// ============================================

// Update progress bar
function updateProgressBar(current, total) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    if (progressFill && progressText) {
        const percent = (current / total) * 100;
        progressFill.style.width = `${percent}%`;
        progressFill.textContent = `${Math.round(percent)}%`;
        progressText.textContent = `Processing response ${current}/${total}...`;
    }
}

// Update main aggregate distribution chart
function updateAggregateChart(aggregatedPMF, totalResponses) {
    const ctx = document.getElementById('distributionChart').getContext('2d');

    const data = {
        labels: ['1 - Strongly Disagree', '2 - Disagree', '3 - Neutral', '4 - Agree', '5 - Strongly Agree'],
        datasets: [{
            label: `Survey Distribution (${totalResponses} respondents)`,
            data: aggregatedPMF.map(p => (p * 100).toFixed(2)),
            backgroundColor: [
                'rgba(239, 68, 68, 0.7)',
                'rgba(251, 146, 60, 0.7)',
                'rgba(250, 204, 21, 0.7)',
                'rgba(34, 197, 94, 0.7)',
                'rgba(34, 211, 238, 0.7)'
            ],
            borderColor: [
                'rgba(239, 68, 68, 1)',
                'rgba(251, 146, 60, 1)',
                'rgba(250, 204, 21, 1)',
                'rgba(34, 197, 94, 1)',
                'rgba(34, 211, 238, 1)'
            ],
            borderWidth: 2
        }]
    };

    const config = {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'Aggregated Survey Distribution',
                    font: { size: 20, weight: 'bold' },
                    color: '#667eea'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y.toFixed(1)}% of respondents`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { callback: value => value + '%' },
                    title: {
                        display: true,
                        text: 'Percentage of Respondents (%)',
                        font: { size: 14, weight: 'bold' }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Likert Scale Rating',
                        font: { size: 14, weight: 'bold' }
                    }
                }
            }
        }
    };

    if (chart) {
        chart.destroy();
    }
    chart = new Chart(ctx, config);
}

// Update statistics cards
function updateStatisticsCards(stats) {
    document.getElementById('surveyMean').textContent = stats.mean.toFixed(2);
    document.getElementById('surveyMode').textContent = stats.mode;
    document.getElementById('surveyStdDev').textContent = stats.stdDev.toFixed(2);
    document.getElementById('surveyTotal').textContent = stats.totalResponses;
}

// Update distribution table
function updateDistributionTable(aggregatedPMF, stats) {
    const tbody = document.getElementById('distributionTableBody');
    tbody.innerHTML = '';

    const labels = ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'];
    let cumulativePercent = 0;

    aggregatedPMF.forEach((prob, idx) => {
        const row = tbody.insertRow();
        const percentage = prob * 100;
        cumulativePercent += percentage;

        row.insertCell(0).textContent = `${idx + 1} - ${labels[idx]}`;
        row.insertCell(1).textContent = stats.levelCounts[idx];
        row.insertCell(2).textContent = `${percentage.toFixed(1)}%`;
        row.insertCell(3).textContent = `${cumulativePercent.toFixed(1)}%`;

        if (idx + 1 === stats.mode) {
            row.style.background = 'rgba(102, 126, 234, 0.15)';
            row.style.fontWeight = 'bold';
        }
    });

    // Also update the total responses display in the header
    const totalDisplay = document.getElementById('totalResponses');
    if (totalDisplay) {
        totalDisplay.textContent = stats.totalResponses;
    }
}

// Export results as CSV
function exportResultsCSV(surveyData, includeDemographics = false) {
    let csv = 'Likert Rating,Label,Probability (%),Estimated Count\\n';
    const labels = ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'];

    surveyData.aggregatedDistribution.forEach((prob, idx) => {
        const count = Math.round(prob * surveyData.totalResponses);
        csv += `${idx + 1},"${labels[idx]}",${(prob * 100).toFixed(2)},${count}\\n`;
    });

    // Add statistics
    const stats = calculateSurveyStatistics(surveyData.aggregatedDistribution, surveyData.totalResponses);
    csv += `\\nSummary Statistics\\n`;
    csv += `Mean,${stats.mean.toFixed(2)}\\n`;
    csv += `Mode,${stats.mode}\\n`;
    csv += `Std Deviation,${stats.stdDev.toFixed(2)}\\n`;
    csv += `Total Responses,${stats.totalResponses}\\n`;

    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ssr-survey-results-${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// ============================================
// MAIN ANALYSIS FUNCTION
// ============================================

async function analyzeSurvey() {
    // Determine which input mode is active (paste or CSV)
    const pasteTab = document.getElementById('pasteTab');
    const csvTab = document.getElementById('csvTab');
    const isCSVMode = csvTab && csvTab.classList.contains('active');

    let responses, demographics, hasDemographics;

    if (isCSVMode) {
        // CSV mode
        const csvText = document.getElementById('csvInput')?.value.trim();
        if (!csvText) {
            alert('Please enter CSV data to analyze.');
            return;
        }

        try {
            const parsed = parseCSV(csvText);
            responses = parsed.responses;
            demographics = parsed.demographics;
            hasDemographics = parsed.hasDemographics;
        } catch (error) {
            alert(`CSV parsing error: ${error.message}`);
            return;
        }
    } else {
        // Paste mode
        const responseText = document.getElementById('responsesInput')?.value.trim();
        if (!responseText) {
            alert('Please enter survey responses to analyze.');
            return;
        }

        responses = parseResponses(responseText);
        hasDemographics = false;
    }

    // Get anchors
    const anchors = [
        document.getElementById('anchor1')?.value.trim(),
        document.getElementById('anchor2')?.value.trim(),
        document.getElementById('anchor3')?.value.trim(),
        document.getElementById('anchor4')?.value.trim(),
        document.getElementById('anchor5')?.value.trim()
    ];

    // Validation
    if (anchors.some(a => !a)) {
        alert('Please fill in all anchor statements.');
        return;
    }

    if (responses.length === 0) {
        alert('No valid responses found. Please enter at least one response.');
        return;
    }

    // Show warning if too few responses
    if (responses.length < 20) {
        const proceed = confirm(`You have ${responses.length} responses. For reliable results matching the research (90% accuracy), 50+ responses are recommended. Continue anyway?`);
        if (!proceed) return;
    }

    // Update UI - show progress, hide results
    const progressContainer = document.getElementById('progressContainer');
    const resultsSection = document.getElementById('results');
    const analyzeBtn = document.getElementById('analyzeSurveyBtn');

    if (progressContainer) progressContainer.classList.add('active');
    if (resultsSection) resultsSection.classList.remove('active');
    if (analyzeBtn) analyzeBtn.disabled = true;

    try {
        // Analyze batch with progress updates
        const surveyData = await analyzeSurveyBatch(responses, anchors, updateProgressBar);
        const stats = calculateSurveyStatistics(surveyData.aggregatedDistribution, surveyData.totalResponses);

        // Store for export
        currentSurveyData = { ...surveyData, hasDemographics, demographics };

        // Update all UI elements
        updateAggregateChart(surveyData.aggregatedDistribution, surveyData.totalResponses);
        updateStatisticsCards(stats);
        updateDistributionTable(surveyData.aggregatedDistribution, stats);

        // Handle demographics if available
        if (hasDemographics && demographics) {
            // TODO: Implement demographic segmentation display
            document.getElementById('demographicSection').style.display = 'block';
        }

        // Show results
        if (resultsSection) resultsSection.classList.add('active');

        // Scroll to results
        setTimeout(() => {
            resultsSection?.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }, 100);

    } catch (error) {
        console.error('Analysis error:', error);
        alert(`Error during analysis: ${error.message}\n\nPlease try again or check the console for details.`);
    } finally {
        if (progressContainer) progressContainer.classList.remove('active');
        if (analyzeBtn) analyzeBtn.disabled = false;
    }
}

// ============================================
// EXAMPLE DATASET
// ============================================

function loadExampleSurvey() {
    // Example survey question
    const exampleQuestion = "How likely are you to purchase this new eco-friendly water bottle made from recycled ocean plastic?";

    // 50 example responses with varied demographics
    const exampleResponses = `I would definitely buy this! The environmental impact really matters to me and I've been looking for a sustainable water bottle option.
Not interested. I already have too many water bottles and the price seems high for what it is.
Maybe, but I'd need to see it in person first. The eco-friendly aspect is nice but I'm concerned about durability.
Absolutely! Supporting ocean cleanup initiatives is important to me and this combines functionality with environmental responsibility.
Probably not. While I appreciate the environmental angle, I prefer stainless steel bottles for temperature control.
I'm very likely to purchase this. It aligns with my values and I'd be happy to pay a premium for sustainable products.
Not for me. I don't really use water bottles that often and when I do, plastic works fine for my needs.
I would consider it, but I'd want to read reviews first to make sure the quality is good despite being made from recycled materials.
Definitely buying this! I love supporting companies that are trying to make a positive environmental impact.
Unlikely. The concept is great but I'm on a tight budget right now and can't justify the expense.
Very interested! I've been trying to reduce my plastic consumption and this seems like a perfect fit.
Not really my thing. I prefer drinking from glasses and don't see myself carrying a water bottle around.
I'd probably buy one. The ocean plastic angle is compelling and I need a new water bottle anyway.
No thanks. I'm skeptical about the actual environmental benefit and whether it's just greenwashing.
Absolutely would purchase! This is exactly the kind of product I want to support with my money.
Maybe in the future, but not right now. I like the idea but have other priorities at the moment.
Very likely to buy. My current bottle is getting old and I'd rather replace it with something eco-friendly.
Not interested at all. Water bottles are water bottles - I don't see why I should pay more for this one.
I would definitely consider it. Anything that helps clean up our oceans gets my attention.
Probably yes, especially if it comes in different colors. The environmental aspect is a nice bonus.
Not for me personally, but I might buy it as a gift for my environmentally conscious friends.
Very likely! I love products that have a story and purpose behind them beyond just functionality.
I'm unsure. The price point matters a lot to me and I'd need to compare it with other options first.
Absolutely would buy this. Ocean pollution is a huge concern and I want to be part of the solution.
Probably not. I already use reusable bottles and don't need another one regardless of what it's made from.
Definitely interested! The combination of environmental benefit and practical use is perfect for me.
Not likely. I tend to lose water bottles so I can't justify spending much on one.
Very interested in this product. I try to make environmentally responsible purchases whenever possible.
Maybe, but I'd want to know more about the company's other environmental practices first.
I would buy it! The eco-friendly materials are important to me and I appreciate innovative recycling solutions.
Not for me. I prefer my current bottle and don't see a compelling reason to switch.
Definitely would purchase. Supporting ocean cleanup and reducing plastic waste are causes I care deeply about.
Unlikely unless it goes on sale. The concept is good but I'm pretty price-sensitive when it comes to these products.
Very likely to buy! I love that it addresses ocean pollution while giving me a functional product I need.
Not interested. I already have several reusable water bottles and don't need more clutter.
I would seriously consider purchasing this. The environmental story resonates with me strongly.
Probably not right now, but I'd keep it in mind for when I do need a new water bottle.
Absolutely! This is the kind of innovative environmental solution we need more of.
Not really. Water bottles aren't a priority for me and I'd rather spend my money elsewhere.
Very interested! I've been wanting to be more environmentally conscious and this is an easy way to start.
Maybe, but I'm worried about the quality. Does recycled ocean plastic hold up as well as regular plastic?
I would definitely buy this. Supporting companies with strong environmental missions is important to me.
Not likely to purchase. I'm happy with my current setup and don't want to change it.
Very interested in buying this! The ocean plastic issue is something I care about and this feels like meaningful action.
Probably yes, though I'd like to see some reviews first. The concept is definitely appealing to me.
Not for me. I think there are better ways to help the environment than buying new products, even eco-friendly ones.
I would absolutely purchase this! It combines practicality with environmental responsibility perfectly.
Unlikely. While I appreciate the sentiment, I don't think individual consumer products make that much difference.
Definitely would buy! I love supporting brands that are genuinely trying to make positive environmental change.
Maybe someday, but not a priority for me right now. I have other things I need to spend money on.`;

    // Load into the paste tab
    document.getElementById('surveyQuestion').value = exampleQuestion;
    document.getElementById('responsesInput').value = exampleResponses;

    // Make sure we're on the paste tab
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector('.tab[data-tab="paste"]').classList.add('active');
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById('pasteTab').classList.add('active');

    // Trigger the response counter update
    const event = new Event('input', { bubbles: true });
    document.getElementById('responsesInput').dispatchEvent(event);

    // Scroll to the input
    document.getElementById('responsesInput').scrollIntoView({ behavior: 'smooth', block: 'center' });

    // Show confirmation
    setTimeout(() => {
        alert('Example survey loaded! This demonstrates 50 synthetic consumer responses about purchasing an eco-friendly water bottle. Click "Analyze Survey" to see the aggregated results.');
    }, 500);
}

// ============================================
// ANCHOR TEMPLATES
// ============================================

const anchorTemplates = {
    purchase: {
        1: "Definitely not, absolutely no, would never buy",
        2: "Probably not, unlikely to purchase",
        3: "Maybe, unsure, need more information",
        4: "Probably yes, likely to purchase",
        5: "Definitely yes, absolutely would buy"
    },
    satisfaction: {
        1: "Very dissatisfied, terrible experience",
        2: "Dissatisfied, poor experience",
        3: "Neutral, average experience",
        4: "Satisfied, good experience",
        5: "Very satisfied, excellent experience"
    },
    agreement: {
        1: "Strongly disagree, completely oppose",
        2: "Disagree, not in favor",
        3: "Neutral, no strong opinion",
        4: "Agree, in favor",
        5: "Strongly agree, completely support"
    },
    frequency: {
        1: "Never, not at all",
        2: "Rarely, almost never",
        3: "Sometimes, occasionally",
        4: "Often, frequently",
        5: "Always, all the time"
    },
    quality: {
        1: "Very poor quality, unacceptable",
        2: "Poor quality, below average",
        3: "Average quality, acceptable",
        4: "Good quality, above average",
        5: "Excellent quality, outstanding"
    }
};

function loadAnchorTemplate(templateName) {
    const template = anchorTemplates[templateName];
    if (!template) return;

    for (let i = 1; i <= 5; i++) {
        const input = document.getElementById(`anchor${i}`);
        if (input) input.value = template[i];
    }
}

// ============================================
// EVENT LISTENERS & INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Main analyze button
    document.getElementById('analyzeSurveyBtn')?.addEventListener('click', analyzeSurvey);

    // Export button
    document.getElementById('exportBtn')?.addEventListener('click', () => {
        if (currentSurveyData) {
            exportResultsCSV(currentSurveyData);
        } else {
            alert('Please analyze a survey first before exporting.');
        }
    });

    // Tab switching
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.getAttribute('data-tab');

            // Update tab buttons
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabName}Tab`)?.classList.add('active');
        });
    });

    // Collapsible sections
    document.querySelectorAll('.collapsible-header').forEach(header => {
        header.addEventListener('click', () => {
            const collapsible = header.parentElement;
            collapsible.classList.toggle('expanded');
        });
    });

    // Anchor template dropdown
    document.getElementById('loadTemplateBtn')?.addEventListener('click', () => {
        const select = document.getElementById('anchorTemplate');
        const templateName = select.value;
        if (templateName) {
            loadAnchorTemplate(templateName);
        } else {
            alert('Please select a template first.');
        }
    });

    // Gender sliders (ensure they sum to 100%)
    const maleSlider = document.getElementById('malePercent');
    const femaleSlider = document.getElementById('femalePercent');
    const otherSlider = document.getElementById('otherPercent');

    function updateGenderValues() {
        document.getElementById('malePercentValue').textContent = maleSlider.value + '%';
        document.getElementById('femalePercentValue').textContent = femaleSlider.value + '%';
        document.getElementById('otherPercentValue').textContent = otherSlider.value + '%';
    }

    maleSlider?.addEventListener('input', updateGenderValues);
    femaleSlider?.addEventListener('input', updateGenderValues);
    otherSlider?.addEventListener('input', updateGenderValues);

    // Generate persona prompts button
    document.getElementById('generatePromptsBtn')?.addEventListener('click', () => {
        const count = parseInt(document.getElementById('personaCount')?.value || 50);
        const surveyQuestion = document.getElementById('surveyQuestion')?.value || '[Your Survey Question]';

        // Get selected age ranges
        const ageRanges = Array.from(document.querySelectorAll('.age-range:checked'))
            .map(cb => cb.value);

        // Get selected income ranges
        const incomeRanges = Array.from(document.querySelectorAll('.income-range:checked'))
            .map(cb => cb.value);

        // Get gender distribution
        const genders = {
            Male: parseInt(maleSlider?.value || 33),
            Female: parseInt(femaleSlider?.value || 34),
            Other: parseInt(otherSlider?.value || 33)
        };

        // Get selected locations
        const locations = Array.from(document.querySelectorAll('.location:checked'))
            .map(cb => cb.value);

        if (ageRanges.length === 0 || incomeRanges.length === 0 || locations.length === 0) {
            alert('Please select at least one option for age, income, and location.');
            return;
        }

        const config = { count, ageRanges, incomeRanges, genders, locations, surveyQuestion };
        const prompts = generatePersonaPrompts(config);

        // Display prompts (show first 5)
        const display = document.getElementById('promptsDisplay');
        if (display) {
            const preview = prompts.slice(0, 5).join('\n\n---\n\n');
            display.value = preview + `\n\n... (${prompts.length - 5} more prompts)\n\n[Click "Copy All Prompts" to copy all ${prompts.length} prompts]`;
        }

        // Store all prompts for copying
        window.generatedPersonaPrompts = prompts;

        // Show the generated prompts section
        document.getElementById('generatedPrompts').style.display = 'block';
        document.getElementById('copyPromptsBtn').disabled = false;
    });

    // Copy prompts button
    document.getElementById('copyPromptsBtn')?.addEventListener('click', () => {
        if (window.generatedPersonaPrompts) {
            copyPersonaPromptsToClipboard(window.generatedPersonaPrompts);
        }
    });

    // Response counter (live update for paste tab)
    document.getElementById('responsesInput')?.addEventListener('input', (e) => {
        const responses = parseResponses(e.target.value);
        const counter = document.getElementById('responseCounter');
        const counterText = document.getElementById('counterText');

        if (counter && counterText) {
            if (responses.length > 0) {
                counter.style.display = 'flex';
                counterText.textContent = `${responses.length} response${responses.length !== 1 ? 's' : ''} detected`;

                if (responses.length < 20) {
                    counter.classList.add('warning');
                    counterText.textContent += ' - Consider using 50+ for best accuracy';
                } else {
                    counter.classList.remove('warning');
                }
            } else {
                counter.style.display = 'none';
            }
        }
    });

    // CSV counter (live update for CSV tab)
    document.getElementById('csvInput')?.addEventListener('input', (e) => {
        try {
            const parsed = parseCSV(e.target.value);
            const counter = document.getElementById('csvCounter');
            const counterText = document.getElementById('csvCounterText');

            if (counter && counterText && parsed.responses.length > 0) {
                counter.style.display = 'flex';
                counterText.textContent = `${parsed.responses.length} response${parsed.responses.length !== 1 ? 's' : ''} detected`;

                if (parsed.hasDemographics) {
                    counterText.textContent += ' (with demographics)';
                    counter.classList.remove('warning');
                } else {
                    counterText.textContent += ' (demographics not detected)';
                }

                if (parsed.responses.length < 20) {
                    counter.classList.add('warning');
                }
            } else if (counter) {
                counter.style.display = 'none';
            }
        } catch (error) {
            // Invalid CSV, hide counter
            const counter = document.getElementById('csvCounter');
            if (counter) counter.style.display = 'none';
        }
    });

    // Load example button
    document.getElementById('loadExampleBtn')?.addEventListener('click', loadExampleSurvey);

    // ============================================
    // B2B PERSONA MODE EVENT HANDLERS
    // ============================================

    // Survey mode toggle (B2C vs B2B)
    document.querySelectorAll('input[name="surveyMode"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            const isB2B = e.target.value === 'b2b';
            const b2bSection = document.getElementById('b2bPersonaSection');
            const b2cSection = document.getElementById('personaGenerator');

            if (b2bSection) b2bSection.style.display = isB2B ? 'block' : 'none';
            if (b2cSection) b2cSection.style.display = isB2B ? 'none' : 'block';
        });
    });

    // Live persona counter for B2B mode
    document.getElementById('personaDefinitionsInput')?.addEventListener('input', (e) => {
        try {
            const personas = parsePersonaDefinitions(e.target.value);
            const counter = document.getElementById('personaCounter');
            const text = document.getElementById('personaCountText');

            if (personas.length > 0 && counter && text) {
                counter.style.display = 'flex';
                counter.classList.remove('warning');
                text.textContent = `${personas.length} persona${personas.length > 1 ? 's' : ''} detected`;
            } else if (counter) {
                counter.style.display = 'none';
            }
        } catch (err) {
            const counter = document.getElementById('personaCounter');
            if (counter) counter.style.display = 'none';
        }
    });

    // Generate B2B prompts button
    document.getElementById('generateB2BPromptsBtn')?.addEventListener('click', () => {
        const personaText = document.getElementById('personaDefinitionsInput')?.value;
        const surveyQ = document.getElementById('surveyQuestion')?.value || '[Your Survey Question]';

        if (!personaText || personaText.trim().length === 0) {
            alert('Please paste your persona table first.');
            return;
        }

        try {
            const personas = parsePersonaDefinitions(personaText);
            const prompts = generateB2BPrompts(personas, surveyQ, 50);

            // Display in existing prompts area (reuse B2C display section)
            const display = document.getElementById('promptsDisplay');
            if (display) {
                const preview = prompts.slice(0, 5).map(p => p.prompt).join('\n\n---\n\n');
                display.value = preview + `\n\n... (${prompts.length - 5} more prompts)\n\n[Click "Copy All Prompts" to copy all ${prompts.length} prompts]`;
            }

            // Store for copying
            window.generatedPersonaPrompts = prompts.map(p => p.prompt);

            // Show the generated prompts section
            document.getElementById('generatedPrompts').style.display = 'block';
            document.getElementById('copyPromptsBtn').disabled = false;

            // Scroll to prompts
            setTimeout(() => {
                document.getElementById('generatedPrompts')?.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest'
                });
            }, 100);

        } catch (error) {
            alert(`Error parsing persona table: ${error.message}\n\nMake sure your table has a "role" or "persona" column.`);
        }
    });

    console.log('SSR Survey Simulator loaded!');
    console.log('Ready to analyze batch responses and generate survey distributions.');
    console.log('All three tiers available: Simple paste, Persona generator, CSV with demographics');
    console.log('B2B persona support: Copy/paste from Excel/Word tables');
});
