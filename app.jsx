import { useEffect, useState } from 'react';
import { supabase } from './supabase';
import './app.css';

function App() {
  const [connectionStatus, setConnectionStatus] = useState('testing');

  useEffect(() => {
    async function testConnection() {
      try {
        const { data, error } = await supabase
          .from('test_table')
          .select('*');

        if (error) {
          console.error('Connection failed:', error);
          setConnectionStatus('failed');
        } else {
          console.log('Connection successful!');
          console.log(data);
          setConnectionStatus('success');
        }
      } catch (e) {
        console.error('Connection error:', e);
        setConnectionStatus('failed');
      }
    }

    testConnection();
  }, []);

  return (
    <div className="cinema-app">
      {/* Header with Logo */}
      <header className="cinema-header">
        <div className="logo-container">
          <img src="/static/logo.svg" alt="Cinema Insight Logo" className="cinema-logo" />
        </div>
      </header>

      {/* Main Content */}
      <main className="cinema-main">
        <div className="welcome-section">
          <h1>Welcome to Cinema Insight</h1>
          <p>Discover, Review & Experience Cinema</p>
        </div>

        {/* Connection Status */}
        <div className={`status-card ${connectionStatus}`}>
          <div className="status-indicator"></div>
          <div className="status-text">
            {connectionStatus === 'testing' && 'Testing database connection...'}
            {connectionStatus === 'success' && '✓ Database connection successful!'}
            {connectionStatus === 'failed' && '✗ Database connection failed'}
          </div>
        </div>

        {/* Features */}
        <section className="features-section">
          <div className="feature-card">
            <i className="fas fa-film"></i>
            <h3>Discover Movies</h3>
            <p>Browse through our extensive collection of films</p>
          </div>
          <div className="feature-card">
            <i className="fas fa-star"></i>
            <h3>Share Reviews</h3>
            <p>Write and read reviews from cinema enthusiasts</p>
          </div>
          <div className="feature-card">
            <i className="fas fa-bookmark"></i>
            <h3>Save Favorites</h3>
            <p>Keep track of movies you want to watch</p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="cinema-footer">
        <p>&copy; 2024 Cinema Insight. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;