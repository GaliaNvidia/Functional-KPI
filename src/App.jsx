import React, { useState, useEffect } from 'react';
import './App.css';

const INITIAL_METRICS = [
  {
    id: 1,
    name: '% of On Time Delivery MP',
    categories: ['Flex', 'Jabil', 'Fabrinet'],
    min: 98,
    target: 100,
    stretch: 100,
    type: 'percentage',
    slides: ['OTD MP- Flex', 'OTD MP- Jabil', 'OTD MP-Fabrinet']
  },
  {
    id: 2,
    name: '% of On Time Delivery - STD RW',
    categories: ['Flex', 'Jabil', 'Fabrinet'],
    min: 98,
    target: 100,
    stretch: 100,
    type: 'percentage',
    slides: ['OTD STD rework-Flex', 'OTD STD rework -Jabil', 'OTD STD rework-Fabrinet']
  },
  {
    id: 3,
    name: '% of Reschedule (Push out) performance in MP',
    categories: ['Flex Boards, Flex SYS+SW', 'Jabil Boards, Jabil SYS+SW', 'Fabrinet Interconnect'],
    min: 3,
    target: 5,
    stretch: 5,
    type: 'number',
    slides: ['RSOD- Flex', 'RSOD-Jabil', 'RSOD-Fabrinet']
  },
  {
    id: 4,
    name: 'Inventory/E&O Reporting and Liability Mitigation',
    categories: ['Flex Boards, Flex SYS+SW', 'Jabil Boards, Jabil SYS+SW', 'Fabrinet Interconnect'],
    min: 4,
    target: 5,
    stretch: 5,
    type: 'number',
    slides: ['Inventory/E&O & Liability-Flex', 'Inventory/E&O & Liability-Jabil', 'Inventory/E&O & Liability-Fabrinet']
  },
  {
    id: 5,
    name: 'Procurement Analytics',
    categories: ['Flex Boards, Flex SYS+SW', 'Jabil Boards, Jabil SYS+SW', 'Fabrinet Interconnect'],
    min: 4,
    target: 5,
    stretch: 5,
    type: 'number',
    slides: ['Proc Analytics-Flex', 'Proc Analytics- Jabil', 'Proc Analytics-Fabrinet']
  },
  {
    id: 6,
    name: 'Materials Escalation & LT Alignment',
    categories: ['Flex Boards, Flex SYS+SW', 'Jabil Boards, Jabil SYS+SW', 'Fabrinet Interconnect'],
    min: 4,
    target: 5,
    stretch: 5,
    type: 'number',
    slides: ['ME & LT-Flex', 'ME & LT- Jabil', 'ME & LT-Fabrinet']
  },
  {
    id: 7,
    name: 'Component PO TAT/Commit Performance',
    categories: ['Flex Boards, Flex SYS+SW', 'Jabil Boards, Jabil SYS+SW', 'Fabrinet Interconnect'],
    min: 4,
    target: 5,
    stretch: 5,
    type: 'number',
    slides: ['Comp. PO Perf.-Flex', 'Comp. PO Perf.-Jabil', 'Comp. PO Perf.-Fabrinet']
  },
  {
    id: 8,
    name: 'New Product Launch Readiness',
    categories: ['Flex Boards, Flex SYS+SW', 'Jabil Boards, Jabil SYS+SW', 'Fabrinet Interconnect'],
    min: 4,
    target: 5,
    stretch: 5,
    type: 'number',
    slides: ['NPL Readiness- Flex', 'NPL Readiness-Jabil', 'NPL Readiness-Fabrinet']
  },
  {
    id: 9,
    name: 'CM Material Audit',
    categories: ['Flex', 'Jabil', 'Fabrinet Interconnect'],
    min: 98,
    target: 100,
    stretch: 100,
    type: 'percentage',
    slides: ['Material audit-Flex', 'Material audit-Jabil', 'Material audit-Fabrinet']
  }
];

function App() {
  const [quarters, setQuarters] = useState([]);
  const [data, setData] = useState({});
  const [editingCell, setEditingCell] = useState(null);
  const [currentQuarter, setCurrentQuarter] = useState('');

  useEffect(() => {
    // Load data from localStorage
    const savedData = localStorage.getItem('kpiData');
    const savedQuarters = localStorage.getItem('kpiQuarters');
    
    if (savedData && savedQuarters) {
      setData(JSON.parse(savedData));
      setQuarters(JSON.parse(savedQuarters));
    } else {
      // Initialize with default quarters
      const defaultQuarters = generateDefaultQuarters();
      setQuarters(defaultQuarters);
      setData({});
    }
  }, []);

  useEffect(() => {
    // Save data to localStorage whenever it changes
    if (Object.keys(data).length > 0 || quarters.length > 0) {
      localStorage.setItem('kpiData', JSON.stringify(data));
      localStorage.setItem('kpiQuarters', JSON.stringify(quarters));
    }
  }, [data, quarters]);

  const generateDefaultQuarters = () => {
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth(); // 0-11
    const currentYear = currentDate.getFullYear();
    
    // Determine fiscal year (FY starts in February)
    let fiscalYear = currentYear;
    if (currentMonth < 1) { // Before February
      fiscalYear = currentYear - 1;
    }
    
    // Determine current fiscal quarter
    let currentFiscalQuarter;
    if (currentMonth >= 1 && currentMonth <= 3) {
      currentFiscalQuarter = 1; // Q1: Feb-Apr
    } else if (currentMonth >= 4 && currentMonth <= 6) {
      currentFiscalQuarter = 2; // Q2: May-Jul
    } else if (currentMonth >= 7 && currentMonth <= 9) {
      currentFiscalQuarter = 3; // Q3: Aug-Oct
    } else {
      currentFiscalQuarter = 4; // Q4: Nov-Jan
    }
    
    const quarters = [];
    for (let i = 3; i >= 0; i--) {
      let q = currentFiscalQuarter - i;
      let fy = fiscalYear;
      
      if (q <= 0) {
        q += 4;
        fy -= 1;
      }
      
      const fyShort = fy % 100;
      quarters.push(`Q${q}FY${fyShort}`);
    }
    
    return quarters;
  };

  const getColorForValue = (value, min, target, stretch, type) => {
    if (value === null || value === undefined || value === '') return '';
    
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return '';
    
    if (type === 'percentage') {
      if (numValue < min) return 'red';
      if (numValue < target) return 'yellow';
      return 'green';
    } else {
      // For regular numbers
      if (numValue < min) return 'red';
      if (numValue < target) return 'yellow';
      return 'green';
    }
  };

  const handleCellClick = (metricId, category, quarter) => {
    setEditingCell({ metricId, category, quarter });
  };

  const handleCellChange = (value) => {
    if (!editingCell) return;
    
    const { metricId, category, quarter } = editingCell;
    const key = `${metricId}-${category}-${quarter}`;
    
    setData(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleCellBlur = () => {
    setEditingCell(null);
  };

  const getCellValue = (metricId, category, quarter) => {
    const key = `${metricId}-${category}-${quarter}`;
    return data[key] || '';
  };

  const addNewQuarter = () => {
    if (!currentQuarter) return;
    
    // Check if quarter already exists
    if (quarters.includes(currentQuarter)) {
      alert('This quarter already exists!');
      return;
    }
    
    const newQuarters = [...quarters, currentQuarter].slice(-4);
    setQuarters(newQuarters);
    setCurrentQuarter('');
  };

  const copyTableToClipboard = () => {
    const table = document.getElementById('kpi-table');
    const range = document.createRange();
    range.selectNode(table);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);
    document.execCommand('copy');
    window.getSelection().removeAllRanges();
    alert('Table copied to clipboard! You can now paste it into PowerPoint.');
  };

  const exportToJSON = () => {
    const exportData = {
      quarters,
      data,
      exportDate: new Date().toISOString()
    };
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'kpi-data.json';
    link.click();
  };

  const importFromJSON = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importData = JSON.parse(e.target.result);
        setQuarters(importData.quarters || []);
        setData(importData.data || {});
        alert('Data imported successfully!');
      } catch (error) {
        alert('Error importing data: ' + error.message);
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>FUNCTIONAL KPI</h1>
          <div className="legend">
            <span className="legend-label">Functional Measures</span>
            <div className="legend-items">
              <div className="legend-item">
                <span className="legend-marker">Min</span>
                <div className="legend-color red"></div>
              </div>
              <div className="legend-item">
                <span className="legend-marker">Target</span>
                <div className="legend-color yellow"></div>
              </div>
              <div className="legend-item">
                <span className="legend-marker">Stretch</span>
                <div className="legend-color green"></div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="controls">
        <div className="quarter-input">
          <input
            type="text"
            value={currentQuarter}
            onChange={(e) => setCurrentQuarter(e.target.value)}
            placeholder="e.g., Q4FY25"
            className="quarter-field"
          />
          <button onClick={addNewQuarter} className="btn btn-primary">Add Quarter</button>
        </div>
        <div className="actions">
          <button onClick={copyTableToClipboard} className="btn btn-secondary">📋 Copy Table</button>
          <button onClick={exportToJSON} className="btn btn-secondary">💾 Export Data</button>
          <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
            📁 Import Data
            <input
              type="file"
              accept=".json"
              onChange={importFromJSON}
              style={{ display: 'none' }}
            />
          </label>
        </div>
      </div>

      <div className="table-container">
        <table id="kpi-table" className="kpi-table">
          <thead>
            <tr>
              <th className="col-number">#</th>
              <th className="col-metrics">Metrics (Measures)</th>
              {quarters.map((quarter) => (
                <th key={quarter} className="col-quarter">{quarter}</th>
              ))}
              <th className="col-threshold">Min/Target/SOL</th>
              <th className="col-slides">Slides</th>
            </tr>
          </thead>
          <tbody>
            {INITIAL_METRICS.map((metric) => (
              <tr key={metric.id}>
                <td className="cell-number">{metric.id}</td>
                <td className="cell-metric">
                  <div className="metric-name">{metric.name}</div>
                  <ul className="category-list">
                    {metric.categories.map((cat, idx) => (
                      <li key={idx}>{cat}</li>
                    ))}
                  </ul>
                </td>
                {quarters.map((quarter) => (
                  <td key={quarter} className="cell-quarter">
                    {metric.categories.map((category, idx) => {
                      const value = getCellValue(metric.id, category, quarter);
                      const isEditing = editingCell?.metricId === metric.id &&
                                       editingCell?.category === category &&
                                       editingCell?.quarter === quarter;
                      const color = getColorForValue(value, metric.min, metric.target, metric.stretch, metric.type);
                      
                      return (
                        <div key={idx} className="category-cell">
                          {isEditing ? (
                            <input
                              type="text"
                              value={value}
                              onChange={(e) => handleCellChange(e.target.value)}
                              onBlur={handleCellBlur}
                              autoFocus
                              className="cell-input"
                            />
                          ) : (
                            <div
                              className={`cell-value ${color}`}
                              onClick={() => handleCellClick(metric.id, category, quarter)}
                            >
                              {value || '-'}
                              {value && metric.type === 'percentage' && '%'}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </td>
                ))}
                <td className="cell-threshold">
                  {metric.min}/{metric.target}/{metric.stretch}
                </td>
                <td className="cell-slides">
                  {metric.slides.map((slide, idx) => (
                    <div key={idx} className="slide-name">{slide}</div>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <footer className="footer">
        <div className="footer-content">
          <span>NVIDIA CONFIDENTIAL. DO NOT DISTRIBUTE.</span>
          <span className="nvidia-logo">🟢 NVIDIA</span>
        </div>
      </footer>
    </div>
  );
}

export default App;

