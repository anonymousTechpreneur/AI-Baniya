// src/LoginPage.js
import React, { useState } from 'react';
import { TextBox } from 'devextreme-react/text-box';
import Button from 'devextreme-react/button';
import 'devextreme/dist/css/dx.light.css';
import './LoginPage.css';
import boy from './boy.jpg'; 
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.post('http://127.0.0.1:8000/login', {
        email,
        password
      });

      if (response.status === 200) {
        navigate('/app');
      }
    } catch (error) {
      if (error.response && error.response.status === 401) {
        setError('Invalid username or password');
      } else {
        console.error('Error:', error);
        setError('An error occurred while validating credentials');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <h2>Welcome to</h2>
      <h1>AI Baniya</h1>
      <div className="avatar">
        <img src={boy} alt="Avatar" /> 
      </div>
      <div className="form">
        <TextBox
          placeholder="Email ID"
          value={email}
          onValueChanged={(e) => setEmail(e.value)}
        />
        <TextBox
          mode="password"
          placeholder="Password"
          value={password}
          onValueChanged={(e) => setPassword(e.value)}
        />
        {error && <p className="error-message">{error}</p>}
        <div className="buttons">
          <Button
            text={loading ? 'Loading...' : 'Login'}
            type="default"
            onClick={handleLogin}
            disabled={loading}
          />
          <Button text="Sign Up" type="default" />
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
