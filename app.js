import { pipeline, cos_sim } from 'https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2';

// Global variables
let extractor = null;
let chart = null;

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

// Calculate cosine similarity between two vectors
function cosineSimilarity(vecA, vecB) {
    return cos_sim(vecA, vecB);
}

// Mean pooling function for sentence embeddings
function meanPooling(embeddings) {
    // embeddings shape: [1, sequence_length, hidden_size]
    const data = embeddings.data;
    const seqLen = embeddings.dims[1];
    const hiddenSize = embeddings.dims[2];

    const result = new Array(hiddenSize).fill(0);

    for (let i = 0; i < seqLen; i++) {
        for (let j = 0; j < hiddenSize; j++) {
            result[j] += data[i * hiddenSize + j];
        }
    }

    // Average
    for (let j = 0; j < hiddenSize; j++) {
        result[j] /= seqLen;
    }

    return result;
}

// Get embedding for a text
async function getEmbedding(text) {
    const model = await initializeModel();
    const output = await model(text, { pooling: 'mean', normalize: true });
    return Array.from(output.data);
}

// SSR Algorithm: Convert text response to Likert distribution
async function semanticSimilarityRating(response, anchors) {
    // Get embeddings for response and all anchors
    const responseEmbedding = await getEmbedding(response);
    const anchorEmbeddings = await Promise.all(
        anchors.map(anchor => getEmbedding(anchor))
    );

    // Calculate cosine similarities
    const similarities = anchorEmbeddings.map(anchorEmb =>
        cosineSimilarity(responseEmbedding, anchorEmb)
    );

    // Apply SSR transformation:
    // 1. Subtract minimum similarity (as per paper's methodology)
    const minSim = Math.min(...similarities);
    const shiftedSims = similarities.map(s => s - minSim);

    // 2. Add small epsilon to avoid division by zero
    const epsilon = 1e-8;
    const regularizedSims = shiftedSims.map(s => s + epsilon);

    // 3. Normalize to get probability distribution
    const sumSims = regularizedSims.reduce((a, b) => a + b, 0);
    const probabilities = regularizedSims.map(s => s / sumSims);

    return {
        similarities: similarities,
        probabilities: probabilities,
        rawSimilarities: similarities
    };
}

// Calculate statistics from probability distribution
function calculateStats(probabilities) {
    // Predicted rating (1-5)
    const predictedRating = probabilities.indexOf(Math.max(...probabilities)) + 1;

    // Confidence (highest probability)
    const confidence = Math.max(...probabilities);

    // Mean score (expected value)
    const mean = probabilities.reduce((sum, prob, idx) => sum + prob * (idx + 1), 0);

    // Standard deviation
    const variance = probabilities.reduce((sum, prob, idx) => {
        const diff = (idx + 1) - mean;
        return sum + prob * diff * diff;
    }, 0);
    const stdDev = Math.sqrt(variance);

    return {
        predictedRating,
        confidence,
        mean,
        stdDev
    };
}

// Create or update the chart
function updateChart(probabilities) {
    const ctx = document.getElementById('distributionChart').getContext('2d');

    const data = {
        labels: ['1 - Strongly Disagree', '2 - Disagree', '3 - Neutral', '4 - Agree', '5 - Strongly Agree'],
        datasets: [{
            label: 'Probability Distribution',
            data: probabilities.map(p => (p * 100).toFixed(2)),
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
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Likert Scale Probability Distribution',
                    font: {
                        size: 18,
                        weight: 'bold'
                    },
                    color: '#667eea'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Probability: ${context.parsed.y}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    title: {
                        display: true,
                        text: 'Probability (%)',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Likert Scale Rating',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    }
                }
            }
        }
    };

    // Destroy existing chart if it exists
    if (chart) {
        chart.destroy();
    }

    chart = new Chart(ctx, config);
}

// Update the distribution table
function updateTable(probabilities, similarities) {
    const tbody = document.getElementById('distributionTableBody');
    tbody.innerHTML = '';

    const labels = ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'];

    probabilities.forEach((prob, idx) => {
        const row = tbody.insertRow();

        const cellRating = row.insertCell(0);
        cellRating.textContent = `${idx + 1} - ${labels[idx]}`;

        const cellProb = row.insertCell(1);
        cellProb.textContent = `${(prob * 100).toFixed(2)}%`;

        const cellSim = row.insertCell(2);
        cellSim.textContent = similarities[idx].toFixed(4);

        // Highlight the highest probability
        if (prob === Math.max(...probabilities)) {
            row.style.background = 'rgba(102, 126, 234, 0.1)';
            row.style.fontWeight = 'bold';
        }
    });
}

// Main analysis function
async function analyzeResponse() {
    const response = document.getElementById('response').value.trim();
    const anchors = [
        document.getElementById('anchor1').value.trim(),
        document.getElementById('anchor2').value.trim(),
        document.getElementById('anchor3').value.trim(),
        document.getElementById('anchor4').value.trim(),
        document.getElementById('anchor5').value.trim()
    ];

    // Validation
    if (!response) {
        alert('Please enter an AI response to analyze.');
        return;
    }

    if (anchors.some(a => !a)) {
        alert('Please fill in all anchor statements.');
        return;
    }

    // Show loading
    document.getElementById('loading').classList.add('active');
    document.getElementById('results').classList.remove('active');
    document.getElementById('analyzeBtn').disabled = true;

    try {
        // Perform SSR analysis
        const result = await semanticSimilarityRating(response, anchors);
        const stats = calculateStats(result.probabilities);

        // Update UI
        document.getElementById('predictedRating').textContent = stats.predictedRating;
        document.getElementById('confidence').textContent = `${(stats.confidence * 100).toFixed(1)}%`;
        document.getElementById('meanScore').textContent = stats.mean.toFixed(2);
        document.getElementById('stdDev').textContent = stats.stdDev.toFixed(2);

        updateChart(result.probabilities);
        updateTable(result.probabilities, result.rawSimilarities);

        // Show results
        document.getElementById('results').classList.add('active');

        // Smooth scroll to results
        setTimeout(() => {
            document.getElementById('results').scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }, 100);

    } catch (error) {
        console.error('Analysis error:', error);
        alert(`Error during analysis: ${error.message}\n\nPlease try again or check the console for details.`);
    } finally {
        // Hide loading
        document.getElementById('loading').classList.remove('active');
        document.getElementById('analyzeBtn').disabled = false;
    }
}

// Load example data
function loadExample() {
    document.getElementById('question').value =
        'How likely are you to purchase this new eco-friendly shampoo that costs $15?';

    document.getElementById('response').value =
        'I find this product quite appealing, especially the eco-friendly aspect which aligns well with my values. The price point of $15 is reasonable for a sustainable product. I would probably purchase it if it\'s available at my local store and has good reviews. The environmental benefits make it worth trying, though I\'d like to see some customer testimonials first.';

    // Scroll to the analyze button
    setTimeout(() => {
        document.getElementById('analyzeBtn').scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }, 100);
}

// Event listeners
document.getElementById('analyzeBtn').addEventListener('click', analyzeResponse);
document.getElementById('exampleBtn').addEventListener('click', loadExample);

// Allow Enter key in textareas (Shift+Enter for new line)
document.querySelectorAll('textarea').forEach(textarea => {
    textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            analyzeResponse();
        }
    });
});

// Initialize on load
console.log('SSR Tool loaded. Ready to analyze responses!');
console.log('Note: First analysis may take a moment while loading the embedding model.');
