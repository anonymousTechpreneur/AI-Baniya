import React from 'react';
import './OrderSummary.css';

function OrderSummary({ orderData = {}, customerData = {} }) {
  const {
    billNo,
    dateTime,
    items = [],
    totalAmount,
    paymentMethod
  } = orderData;

  const {
    CustomerId,
    Name,
    PhoneNumber,
    EmailId,
    Address,
    GSTNumber
  } = customerData;

  return (
    <div className="order-summary">
      <div className="header">Order Summary</div>

      <div className="top-section">
        <div className="customer-info section">
          <div className="section-header">Customer Information</div>
          <div className="section-content">
            {CustomerId && <div><strong>Customer ID:</strong> {CustomerId}</div>}
            {Name && <div><strong>Name:</strong> {Name}</div>}
            {PhoneNumber && <div><strong>Phone:</strong> {PhoneNumber}</div>}
            {EmailId && <div><strong>Email:</strong> {EmailId}</div>}
            {Address && <div><strong>Address:</strong> {Address}</div>}
            {GSTNumber && <div><strong>GST Number:</strong> {GSTNumber}</div>}
          </div>
        </div>
        
        <div className="bill-info section">
          <div className="section-header">Billing Information</div>
          <div className="section-content">
            {billNo && <div><strong>Bill No:</strong> {billNo}</div>}
            {dateTime && <div><strong>Date Time:</strong> {dateTime}</div>}
          </div>
        </div>
      </div>

      <div className="section">
        <div className="section-header">Order Details</div>
        <div className="section-content">
          <table className="order-details-table">
            <thead>
              <tr>
                <th>Product Name</th>
                <th>SKU</th>
                <th>Availability</th>
                <th>Quantity</th>
                <th>Price</th>
                <th>Order Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={index}>
                  <td>{item.productName}</td>
                  <td>{item.sku}</td>
                  <td>{item.availability}</td>
                  <td>{item.quantity}</td>
                  <td>${item.price}</td>
                  <td>${item.subtotal}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="payment-detail section">
        <div className="section-header">Payment Details</div>
        <div className="section-content">
          {totalAmount && <div><strong>Total Amount:</strong> ${totalAmount}</div>}
          {paymentMethod && <div><strong>Payment Method:</strong> {paymentMethod}</div>}
        </div>
      </div>
      
      <div className="order-actions">
        <button className="btn back-btn">Back</button>
        <button className="btn order-btn">Order</button>
      </div>
    </div>
  );
}

export default OrderSummary;
