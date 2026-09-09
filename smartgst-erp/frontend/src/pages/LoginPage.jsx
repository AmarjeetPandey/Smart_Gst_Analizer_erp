import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState('email'); // 'email' or 'otp'
  const [isLoading, setIsLoading] = useState(false);
  const { sendOTP, login } = useAuth();
  const navigate = useNavigate();

  const handleSendOTP = async (e) => {
    e.preventDefault();
    if (!email) {
      toast.error('Please enter your email');
      return;
    }

    setIsLoading(true);
    try {
      await sendOTP(email);
      toast.success('OTP sent to your email');
      setStep('otp');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    if (!otp) {
      toast.error('Please enter the OTP');
      return;
    }

    setIsLoading(true);
    try {
      await login(email, otp);
      toast.success('Login successful');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid OTP');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-900 flex items-center justify-center px-4">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">SmartGST AI ERP</h1>
          <p className="text-gray-600 mt-2">Business Management Platform</p>
        </div>

        {step === 'email' ? (
          <form onSubmit={handleSendOTP}>
            <div className="mb-6">
              <label className="block text-gray-700 font-medium mb-2">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                placeholder="Enter your email"
                disabled={isLoading}
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full"
            >
              {isLoading ? 'Sending...' : 'Send OTP'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOTP}>
            <div className="mb-4">
              <p className="text-gray-600 text-sm">OTP sent to: <strong>{email}</strong></p>
            </div>
            <div className="mb-6">
              <label className="block text-gray-700 font-medium mb-2">Enter OTP</label>
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value.slice(0, 6))}
                className="input-field text-center text-2xl tracking-widest"
                placeholder="000000"
                maxLength="6"
                disabled={isLoading}
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full"
            >
              {isLoading ? 'Verifying...' : 'Verify OTP'}
            </button>
            <button
              type="button"
              onClick={() => {
                setStep('email');
                setOtp('');
              }}
              className="btn-secondary w-full mt-2"
              disabled={isLoading}
            >
              Back
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default LoginPage;
