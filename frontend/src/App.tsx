import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface ContentType {
  value: string;
  label: string;
  description: string;
}

const contentTypes: ContentType[] = [
  {
    value: 'quiz',
    label: 'Quiz',
    description: 'Interactive quizzes with multiple choice questions',
  },
  {
    value: 'quest_game',
    label: 'Quest Game',
    description: 'Quest-based adventure games with choices and rewards',
  },
  {
    value: 'branched_narrative',
    label: 'Branched Story',
    description: 'Branching storylines with multiple endings',
  },
  {
    value: 'web_simulation',
    label: 'Simulation',
    description: 'Interactive simulations with variables and controls',
  },
];

function App() {
  const [selectedType, setSelectedType] = useState<string>('quiz');
  const [topic, setTopic] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>('');

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/generate`, {
        content_type: selectedType,
        topic: topic,
        parameters: {},
      });

      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate content. Please try again.');
      console.error('Error generating content:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <div className="header">
        <h1>🤖 ADK Agentic Writer</h1>
        <p>Multi-Agentic Interactive Content Production System</p>
      </div>

      <div className="content-selector">
        <h2>Select Content Type</h2>
        <div className="content-types">
          {contentTypes.map((type) => (
            <div
              key={type.value}
              className={`content-type-card ${selectedType === type.value ? 'selected' : ''}`}
              onClick={() => setSelectedType(type.value)}
            >
              <h3>{type.label}</h3>
              <p>{type.description}</p>
            </div>
          ))}
        </div>

        <div className="input-section">
          <label htmlFor="topic">Topic</label>
          <input
            id="topic"
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Enter a topic (e.g., 'Ancient Rome', 'Climate Change', 'Space Exploration')"
            onKeyPress={(e) => e.key === 'Enter' && handleGenerate()}
          />
        </div>

        <button
          className="generate-button"
          onClick={handleGenerate}
          disabled={loading || !topic.trim()}
        >
          {loading ? 'Generating...' : 'Generate Content'}
        </button>

        {error && <div className="error">{error}</div>}
      </div>

      {loading && (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Our team of AI agents is working on your content...</p>
        </div>
      )}

      {result && !loading && (
        <div className="result-container">
          <h2>Generated Content</h2>
          
          {result.agents_involved && result.agents_involved.length > 0 && (
            <div className="agent-status">
              <h4>Agents Involved:</h4>
              <ul className="agent-list">
                {result.agents_involved.map((agent: string, index: number) => (
                  <li key={index} className="agent-badge">
                    {agent.replace('_', ' ')}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="result-content">
            <pre>{JSON.stringify(result.content, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
