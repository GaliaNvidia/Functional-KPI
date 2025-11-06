const { useState, useEffect } = React;

// Default metrics configuration
const DEFAULT_METRICS = [
    {
        id: 1,
        name: "% of On Time Delivery MP",
        details: ["Flex", "Jabil", "Fabrinet"],
        min: 98,
        target: 100,
        stretch: 100,
        unit: "%",
        slides: ["OTD MP- Flex", "OTD MP- Jabil", "OTD MP-Fabrinet"]
    },
    {
        id: 2,
        name: "% of On Time Delivery - STD RW",
        details: ["Flex", "Jabil", "Fabrinet"],
        min: 98,
        target: 100,
        stretch: 100,
        unit: "%",
        slides: ["OTD STD rework-Flex", "OTD STD rework -Jabil", "OTD STD rework-Fabrinet"]
    },
    {
        id: 3,
        name: "% of Reschedule (Push out) performance in MP",
        details: ["Flex Boards, Flex SYS+SW", "Jabil Boards, Jabil SYS+SW", "Fabrinet Interconnect"],
        min: 3,
        target: 5,
        stretch: 5,
        unit: "",
        slides: ["RSOD- Flex", "RSOD-Jabil", "RSOD-Fabrinet"]
    },
    {
        id: 4,
        name: "Inventory/E&O Reporting and Liability Mitigation",
        details: ["Flex Boards, Flex SYS+SW", "Jabil Boards, Jabil SYS+SW", "Fabrinet Interconnect"],
        min: 4,
        target: 5,
        stretch: 5,
        unit: "",
        slides: ["Inventory/E&O & Liability-Flex", "Inventory/E&O & Liability-Jabil", "Inventory/E&O & Liability Fabrinet"]
    },
    {
        id: 5,
        name: "Procurement Analytics",
        details: ["Flex Boards, Flex SYS+SW", "Jabil Boards, Jabil SYS+SW", "Fabrinet Interconnect"],
        min: 4,
        target: 5,
        stretch: 5,
        unit: "",
        slides: ["Proc Analytics-Flex", "Proc Analytics- Jabil", "Proc Analytics-Fabrinet"]
    },
    {
        id: 6,
        name: "Materials Escalation & LT Alignment",
        details: ["Flex Boards, Flex SYS+SW", "Jabil Boards, Jabil SYS+SW", "Fabrinet Interconnect"],
        min: 4,
        target: 5,
        stretch: 5,
        unit: "",
        slides: ["ME & LT-Flex", "ME & LT- Jabil", "ME & LT-Fabrinet"]
    },
    {
        id: 7,
        name: "Component PO TAT/Commit Performance",
        details: ["Flex Boards, Flex SYS+SW", "Jabil Boards, Jabil SYS+SW", "Fabrinet Interconnect"],
        min: 4,
        target: 5,
        stretch: 5,
        unit: "",
        slides: ["Comp. PO Perf.-Flex", "Comp. PO Perf.-Jabil", "Comp. PO Perf.-Fabrinet"]
    },
    {
        id: 8,
        name: "New Product Launch Readiness",
        details: ["Flex Boards, Flex SYS+SW", "Jabil Boards, Jabil SYS+SW", "Fabrinet Interconnect"],
        min: 4,
        target: 5,
        stretch: 5,
        unit: "",
        slides: ["NPL Readiness- Flex", "NPL Readiness-Jabil", "NPL Readiness-Fabrinet"]
    },
    {
        id: 9,
        name: "CM Material Audit",
        details: ["Flex", "Jabil", "Fabrinet Interconnect"],
        min: 98,
        target: 100,
        stretch: 100,
        unit: "%",
        slides: ["Material audit-Flex", "Material audit-Jabil", "Material audit-Fabrinet"]
    }
];

function App() {
    const [metrics, setMetrics] = useState(DEFAULT_METRICS);
    const [quarters, setQuarters] = useState([]);
    const [scores, setScores] = useState({});
    const [editingCell, setEditingCell] = useState(null);
    const [showAddQuarter, setShowAddQuarter] = useState(false);
    const [showToast, setShowToast] = useState(false);
    const [toastMessage, setToastMessage] = useState("");

    // Load data from localStorage on mount
    useEffect(() => {
        const savedData = localStorage.getItem('kpiData');
        if (savedData) {
            const { quarters: savedQuarters, scores: savedScores } = JSON.parse(savedData);
            setQuarters(savedQuarters);
            setScores(savedScores);
        } else {
            // Initialize with sample data
            initializeSampleData();
        }
    }, []);

    // Save data to localStorage whenever it changes
    useEffect(() => {
        if (quarters.length > 0) {
            localStorage.setItem('kpiData', JSON.stringify({ quarters, scores }));
        }
    }, [quarters, scores]);

    const initializeSampleData() {
        const sampleQuarters = ['Q4FY25', 'Q1FY26', 'Q2FY26', 'Q3Y26'];
        const sampleScores = {
            '1-Q4FY25': '99.52',
            '1-Q1FY26': '99.16',
            '1-Q2FY26': '99.38',
            '2-Q4FY25': '100',
            '2-Q1FY26': '100',
            '2-Q2FY26': '100',
            '3-Q4FY25': '3.8',
            '3-Q1FY26': '3.85',
            '3-Q2FY26': '3.92',
            '4-Q4FY25': '5',
            '4-Q1FY26': '4.5',
            '4-Q2FY26': '5',
            '5-Q4FY25': '4.8',
            '5-Q1FY26': '4.8',
            '5-Q2FY26': '4.5',
        };
        setQuarters(sampleQuarters);
        setScores(sampleScores);
    };

    const getColor = (value, metric) => {
        if (!value || value === '') return 'transparent';
        
        const numValue = parseFloat(value);
        if (isNaN(numValue)) return 'transparent';

        const { min, target, stretch } = metric;

        // For percentage metrics (higher is better)
        if (metric.unit === '%') {
            if (numValue < min) return '#ef4444'; // Red
            if (numValue < target) return '#fbbf24'; // Yellow
            return '#86efac'; // Green
        } else {
            // For rating metrics (1-5 scale)
            if (numValue < min) return '#ef4444'; // Red
            if (numValue < target) return '#fbbf24'; // Yellow
            return '#86efac'; // Green
        }
    };

    const handleCellClick = (metricId, quarter) => {
        setEditingCell({ metricId, quarter });
    };

    const handleScoreChange = (metricId, quarter, value) => {
        const key = `${metricId}-${quarter}`;
        setScores(prev => ({
            ...prev,
            [key]: value
        }));
    };

    const handleCellBlur = () => {
        setEditingCell(null);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            setEditingCell(null);
        }
    };

    const addQuarter = (newQuarter) => {
        setQuarters(prev => {
            const updated = [...prev, newQuarter];
            // Keep only last 4 quarters
            return updated.slice(-4);
        });
        setShowAddQuarter(false);
        showToastMessage(`Quarter ${newQuarter} added successfully!`);
    };

    const showToastMessage = (message) => {
        setToastMessage(message);
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3000);
    };

    const copyTableToClipboard = () => {
        const table = document.querySelector('.kpi-table');
        const range = document.createRange();
        range.selectNode(table);
        window.getSelection().removeAllRanges();
        window.getSelection().addRange(range);
        document.execCommand('copy');
        window.getSelection().removeAllRanges();
        showToastMessage('Table copied to clipboard! Ready to paste into your presentation.');
    };

    const exportToCSV = () => {
        let csv = 'Metric,';
        csv += quarters.join(',') + ',Min/Target/Stretch\n';
        
        metrics.forEach(metric => {
            csv += `"${metric.name}",`;
            quarters.forEach(quarter => {
                const key = `${metric.id}-${quarter}`;
                csv += `${scores[key] || ''},`;
            });
            csv += `${metric.min}/${metric.target}/${metric.stretch}\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'kpi-data.csv';
        a.click();
        showToastMessage('Data exported to CSV!');
    };

    const clearAllData = () => {
        if (confirm('Are you sure you want to clear all data? This cannot be undone.')) {
            setScores({});
            setQuarters([]);
            localStorage.removeItem('kpiData');
            showToastMessage('All data cleared!');
        }
    };

    return (
        <div className="container">
            <div className="header">
                <h1>FUNCTIONAL KPI</h1>
                <div className="legend">
                    <span className="legend-title">Functional Measures</span>
                    <div className="legend-item">
                        <div className="legend-bar color-red"></div>
                        <span className="legend-label">Min</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-bar color-yellow"></div>
                        <span className="legend-label">Target</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-bar color-green"></div>
                        <span className="legend-label">Stretch</span>
                    </div>
                </div>
            </div>

            <div className="controls">
                <button className="btn btn-primary" onClick={() => setShowAddQuarter(true)}>
                    ➕ Add Quarter
                </button>
                <button className="btn btn-success" onClick={copyTableToClipboard}>
                    📋 Copy to Clipboard
                </button>
                <button className="btn btn-secondary" onClick={exportToCSV}>
                    📊 Export to CSV
                </button>
                <button className="btn btn-secondary" onClick={clearAllData}>
                    🗑️ Clear All Data
                </button>
            </div>

            <div className="table-container">
                <table className="kpi-table">
                    <thead>
                        <tr>
                            <th className="index-cell">#</th>
                            <th style={{minWidth: '300px'}}>Metrics (Measures)</th>
                            {quarters.map(quarter => (
                                <th key={quarter} className="quarter-header">{quarter}</th>
                            ))}
                            <th>Min/Target/Stretch</th>
                            <th style={{minWidth: '200px'}}>Slides</th>
                        </tr>
                    </thead>
                    <tbody>
                        {metrics.map(metric => (
                            <tr key={metric.id}>
                                <td className="index-cell">{metric.id}</td>
                                <td className="metric-cell">
                                    <div className="metric-name">{metric.name}</div>
                                    <ul className="metric-details">
                                        {metric.details.map((detail, idx) => (
                                            <li key={idx}>{detail}</li>
                                        ))}
                                    </ul>
                                </td>
                                {quarters.map(quarter => {
                                    const key = `${metric.id}-${quarter}`;
                                    const value = scores[key] || '';
                                    const isEditing = editingCell?.metricId === metric.id && editingCell?.quarter === quarter;
                                    const bgColor = getColor(value, metric);

                                    return (
                                        <td
                                            key={quarter}
                                            className="score-cell editable"
                                            style={{ backgroundColor: bgColor }}
                                            onClick={() => handleCellClick(metric.id, quarter)}
                                        >
                                            {isEditing ? (
                                                <input
                                                    type="text"
                                                    className="score-input"
                                                    value={value}
                                                    onChange={(e) => handleScoreChange(metric.id, quarter, e.target.value)}
                                                    onBlur={handleCellBlur}
                                                    onKeyPress={handleKeyPress}
                                                    autoFocus
                                                />
                                            ) : (
                                                value + (value ? metric.unit : '')
                                            )}
                                        </td>
                                    );
                                })}
                                <td className="threshold-cell">
                                    {metric.min}/{metric.target}/{metric.stretch}
                                </td>
                                <td className="slides-cell">
                                    <ul className="slides-list">
                                        {metric.slides.map((slide, idx) => (
                                            <li key={idx}>{slide}</li>
                                        ))}
                                    </ul>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {showAddQuarter && (
                <AddQuarterModal
                    onClose={() => setShowAddQuarter(false)}
                    onAdd={addQuarter}
                />
            )}

            {showToast && (
                <div className="toast">{toastMessage}</div>
            )}
        </div>
    );
}

function AddQuarterModal({ onClose, onAdd }) {
    const [quarter, setQuarter] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (quarter.trim()) {
            onAdd(quarter.trim());
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <h2>Add New Quarter</h2>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Quarter Name (e.g., Q4FY26)</label>
                        <input
                            type="text"
                            value={quarter}
                            onChange={(e) => setQuarter(e.target.value)}
                            placeholder="Q4FY26"
                            autoFocus
                        />
                    </div>
                    <div className="modal-actions">
                        <button type="button" className="btn btn-secondary" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="btn btn-primary">
                            Add Quarter
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));


