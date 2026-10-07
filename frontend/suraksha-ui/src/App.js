import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Dashboard from './pages/Dashboard';
import TransactionDetail from './pages/TransactionDetail';
import AdminPanel from './pages/AdminPanel';
import ConsentPortal from './pages/ConsentPortal';
import DriftMonitor from './pages/DriftMonitor';

const App = () => {
    return (
        <Router>
            <div style={{
                fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
                display: 'flex',
                flexDirection: 'column',
                minHeight: '100vh',
            }}>
                <Navbar />
                <div style={{ flex: 1 }}>
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/transactions" element={<Dashboard />} />
                        <Route path="/transaction/:txnId" element={<TransactionDetail />} />
                        <Route path="/admin" element={<AdminPanel />} />
                        <Route path="/consent" element={<ConsentPortal />} />
                        <Route path="/drift" element={<DriftMonitor />} />
                    </Routes>
                </div>
                <Footer />
            </div>
        </Router>
    );
};

export default App;