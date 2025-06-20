import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { PermissionsProvider } from './contexts/PermissionsContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Search from './pages/Search';
import Upload from './pages/Upload';
import Documents from './pages/Documents';
import Users from './pages/Users';
import ProtectedRoute from './components/ProtectedRoute';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './index.css';
import 'animate.css';

// Make toast available globally
window.toast = toast;

// Auth layout - no navbar or footer
const AuthLayout = ({ children }) => {
  return <>{children}</>;
};

// Main layout - includes navbar and footer
const MainLayout = ({ children }) => {
  return (
    <>
      <Navbar />
      <main className="flex-grow-1 main-content">
        {children}
      </main>
      <Footer />
    </>
  );
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <PermissionsProvider>
          <div className="d-flex flex-column min-vh-100">
            <main className="flex-grow-1 py-4">
              <Routes>
                {/* Auth routes - no navbar/footer */}
                <Route path="/login" element={
                  <AuthLayout>
                    <Login />
                  </AuthLayout>
                } />
                <Route path="/register" element={
                  <AuthLayout>
                    <Register />
                  </AuthLayout>
                } />
                
                {/* Main routes - with navbar/footer */}
                <Route path="/" element={
                  <ProtectedRoute>
                    <MainLayout>
                      <Home />
                    </MainLayout>
                  </ProtectedRoute>
                } />
                <Route path="/search" element={
                  <ProtectedRoute>
                    <MainLayout>
                      <Search />
                    </MainLayout>
                  </ProtectedRoute>
                } />
                <Route path="/upload" element={
                  <ProtectedRoute requiredPermission="can_upload">
                    <MainLayout>
                      <Upload />
                    </MainLayout>
                  </ProtectedRoute>
                } />
                <Route path="/documents" element={
                  <ProtectedRoute requiredPermission="can_manage">
                    <MainLayout>
                      <Documents />
                    </MainLayout>
                  </ProtectedRoute>
                } />
                <Route path="/users" element={
                  <ProtectedRoute requiredPermission="can_manage_users">
                    <MainLayout>
                      <Users />
                    </MainLayout>
                  </ProtectedRoute>
                } />
              </Routes>
            </main>
            <ToastContainer position="bottom-right" />
          </div>
        </PermissionsProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
