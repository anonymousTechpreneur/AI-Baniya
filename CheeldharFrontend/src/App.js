// src/App.js
import React, { useState } from 'react';
import ChatPage from './ChatPage';
import OrderSummary from './OrderSummary';
import './App.css';

function App() {
  const [orderData, setOrderData] = useState({});
  const [customerData, setCustomerData] = useState({
    CustomerId: '',
    Name: '',
    PhoneNumber: '',
    EmailId: '',
    Address: '',
    GSTNumber: '',
  });

  return (
    <div className="app-container">
      <div className="order-summary-container">
        <OrderSummary orderData={orderData} customerData={customerData} />
      </div>
      <div className="chat-page-container">
        <ChatPage setOrderData={setOrderData} setCustomerData={setCustomerData} />
      </div>
    </div>
  );
}

export default App;
