import React, { useState, useRef } from 'react';
import './ChatPage.css';
import { TextBox } from 'devextreme-react/text-box';
import Button from 'devextreme-react/button';
import microphoneIcon from './microphone-icon.jpg';
import stopIcon from './stop-icon.jpg';
import sendIcon from './send-icon.jpg'; // Add your send icon here
import axios from 'axios';

function ChatPage({ setOrderData, setCustomerData }) {
  const [messages, setMessages] = useState([
    { user: 'Bot', text: 'Hello User, welcome to AI Baniya' }
  ]);
  const [currentStep, setCurrentStep] = useState(null);
  const [formData, setFormData] = useState({});
  const [isAddingCustomer, setIsAddingCustomer] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);

  const steps = [
    'Customer Name',
    'Phone Number',
    'Email',
    'Address',
    'GST Number'
  ];

  const handleSend = (text) => {
    if (text) {
      setMessages(prevMessages => [...prevMessages, { user: 'You', text }]);
      handleUserInput(text);
    }
  };

  const handleUserInput = (text) => {
    if (isAddingCustomer) {
      if (currentStep === null) {
        const stepIndex = steps.length - 1;
        const stepName = steps[stepIndex];
        const updatedFormData = { ...formData, [stepName]: text };
        setFormData(updatedFormData);
        setCustomerData(updatedFormData);

        setMessages(prevMessages => [
          ...prevMessages,
          { user: 'Bot', text: 'Customer added successfully!' },
          { user: 'Bot', text: 'Please verify customer details:' }
        ]);

        const details = steps.map(step => (
          <div key={step} className="form-detail">
            <strong>{step}:</strong> {updatedFormData[step] || 'Not provided'}
          </div>
        ));
        setMessages(prevMessages => [
          ...prevMessages,
          { user: 'Bot', text: <div>{details}</div> }
        ]);

        setIsVerifying(true);
        setIsAddingCustomer(false);
        setCurrentStep(null);
      } else {
        const stepIndex = currentStep;
        const stepName = steps[stepIndex];
        const updatedFormData = { ...formData, [stepName]: text };
        setFormData(updatedFormData);

        if (stepIndex < steps.length - 1) {
          setCurrentStep(stepIndex + 1);
          setMessages(prevMessages => [
            ...prevMessages,
            { user: 'Bot', text: `Please enter the ${steps[stepIndex + 1]}.` }
          ]);
        } else {
          setCustomerData(updatedFormData);

          setMessages(prevMessages => [
            ...prevMessages,
            { user: 'Bot', text: 'Customer added successfully!' },
            { user: 'Bot', text: 'Please verify customer details:' }
          ]);

          const details = steps.map(step => (
            <div key={step} className="form-detail">
              <strong>{step}:</strong> {updatedFormData[step] || 'Not provided'}
            </div>
          ));
          setMessages(prevMessages => [
            ...prevMessages,
            { user: 'Bot', text: <div>{details}</div> }
          ]);

          setIsVerifying(true);
          setIsAddingCustomer(false);
          setCurrentStep(null);
        }
      }
    }
  };

  const startRecording = () => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
          mediaRecorderRef.current = new MediaRecorder(stream);
          mediaRecorderRef.current.ondataavailable = (event) => {
            if (event.data.size > 0) {
              const audioBlob = new Blob([event.data], { type: 'audio/wav' });
              uploadAudio(audioBlob);
            }
          };
          mediaRecorderRef.current.start();
          setIsRecording(true);
        })
        .catch(error => {
          console.error('Error accessing microphone:', error);
          setMessages(prevMessages => [
            ...prevMessages,
            { user: 'Bot', text: 'Sorry, there was an error accessing your microphone.' }
          ]);
        });
    } else {
      setMessages(prevMessages => [
        ...prevMessages,
        { user: 'Bot', text: 'Your browser does not support audio recording.' }
      ]);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const uploadAudio = async (audioBlob) => {
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'audio.wav');

      const response = await axios.post('http://127.0.0.1:8000/chatbot', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log(response);

      const data = response.data;

      if (typeof data === 'string') {
        data = JSON.parse(data);
      }

      const customerDetails = data.details;
      
      const formattedDetails = {
        CustomerId: customerDetails.CustomerId[0],
        Name: customerDetails.Name[0],
        PhoneNumber: customerDetails.PhoneNumber[0],
        EmailId: customerDetails.EmailId[0],
        Address: customerDetails.Address[0],
        GSTNumber: customerDetails.GSTNumber[0],
        NameAudioFile: customerDetails.NameAudioFile[0],
        CustomerImageFile: customerDetails.CustomerImageFile[0],
      };

      setCustomerData(formattedDetails);

      setMessages(prevMessages => [
        ...prevMessages,
        { user: 'Bot', text: 'Operation successful' },
        { user: 'Bot', text: 'Customer details:' }
      ]);

      const details = Object.keys(formattedDetails).map(key => (
        <div key={key} className="form-detail">
          <strong>{key}:</strong> {formattedDetails[key] || 'Not provided'}
        </div>
      ));

      setMessages(prevMessages => [
        ...prevMessages,
        { user: 'Bot', text: <div>{details}</div> }
      ]);
    } catch (error) {
      console.error('Error uploading audio:', error);
      setMessages(prevMessages => [
        ...prevMessages,
        { user: 'Bot', text: 'Sorry, there was an error processing your audio.' }
      ]);
    }
  };

  return (
    <div className="chat-container">
      <div className="header">Adbhut banIya</div>
      <div className="chat-screen">
        {messages.map((msg, index) => (
          <div key={index} className="message">
            {msg.user === 'Bot' ? (
              <div className="bot-message">
                {typeof msg.text === 'string' ? (
                  msg.text
                ) : (
                  <div>{msg.text}</div>
                )}
              </div>
            ) : (
              <div className="user-message">
                <strong>{msg.user}:</strong> {msg.text}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="input-container">
        {isRecording ? (
          <img
            src={stopIcon}
            alt="Stop Recording"
            className="microphone-icon"
            onClick={stopRecording}
          />
        ) : (
          <img
            src={microphoneIcon}
            alt="Microphone"
            className="microphone-icon"
            onClick={startRecording}
          />
        )}
        <TextBox
          placeholder="Type your message here..."
          onEnterKey={(e) => handleSend(e.event.target.value)}
        />
        <Button
          icon="send"
          onClick={() => {
            const input = document.querySelector('.dx-texteditor-input');
            handleSend(input.value);
            input.value = '';
          }}
        >
          <img src={sendIcon} alt="Send" className="send-icon" />
        </Button>
      </div>
    </div>
  );
}

export default ChatPage;