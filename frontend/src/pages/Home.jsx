import React from 'react';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faFileUpload, 
  faSearch, 
  faDatabase, 
  faArrowRight, 
  faBookReader,
  faLightbulb,
  faRocket
} from '@fortawesome/free-solid-svg-icons';

const Home = () => {
  return (
    <div className="home-page">
      {/* Hero Section with Gradient Background */}
      <div className="hero-section text-center py-5 mb-5">
        <div className="container">
          <h1 className="display-4 fw-bold mb-4 animate__animated animate__fadeIn">
            PDF Knowledge Base
          </h1>
          <p className="lead mb-5 animate__animated animate__fadeIn animate__delay-1s">
            Upload, search, and manage your PDF documents with ease. 
            Extract knowledge and find information quickly.
          </p>
          
          <div className="row justify-content-center animate__animated animate__fadeInUp animate__delay-1s">
            <div className="col-md-8">
              <div className="card bg-white shadow-lg border-0 mb-4">
                <div className="card-body p-4">
                  <p className="text-muted mb-4">
                    Get started by uploading your first PDF document or searching through your existing knowledge base.
                  </p>
                  <div className="d-flex flex-wrap justify-content-center gap-3">
                    <Link to="/upload" className="btn btn-primary btn-lg px-4 py-3">
                      <FontAwesomeIcon icon={faFileUpload} className="me-2" />
                      Upload Documents
                    </Link>
                    <Link to="/search" className="btn btn-outline-primary btn-lg px-4 py-3">
                      <FontAwesomeIcon icon={faSearch} className="me-2" />
                      Search Knowledge Base
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section with Cards */}
      <div className="container mb-5">
        <div className="row g-4">
          <div className="col-md-4">
            <div className="card h-100 border-0 shadow-sm hover-card">
              <div className="card-body text-center p-4">
                <div className="feature-icon-wrapper mb-3">
                  <FontAwesomeIcon icon={faFileUpload} className="feature-icon text-primary" />
                </div>
                <h3 className="card-title h4 mb-3">Upload PDFs</h3>
                <p className="card-text text-muted">
                  Upload your PDF documents to build your knowledge base. Our system will process and index 
                  the content for easy searching.
                </p>
                <Link to="/upload" className="btn btn-light mt-3">
                  Upload Now <FontAwesomeIcon icon={faArrowRight} className="ms-2" />
                </Link>
              </div>
            </div>
          </div>
          
          <div className="col-md-4">
            <div className="card h-100 border-0 shadow-sm hover-card">
              <div className="card-body text-center p-4">
                <div className="feature-icon-wrapper mb-3">
                  <FontAwesomeIcon icon={faSearch} className="feature-icon text-primary" />
                </div>
                <h3 className="card-title h4 mb-3">Search Content</h3>
                <p className="card-text text-muted">
                  Quickly find information across all your documents with our powerful search functionality. 
                  Get relevant results instantly.
                </p>
                <Link to="/search" className="btn btn-light mt-3">
                  Search Now <FontAwesomeIcon icon={faArrowRight} className="ms-2" />
                </Link>
              </div>
            </div>
          </div>
          
          <div className="col-md-4">
            <div className="card h-100 border-0 shadow-sm hover-card">
              <div className="card-body text-center p-4">
                <div className="feature-icon-wrapper mb-3">
                  <FontAwesomeIcon icon={faDatabase} className="feature-icon text-primary" />
                </div>
                <h3 className="card-title h4 mb-3">Manage Documents</h3>
                <p className="card-text text-muted">
                  Organize, update, and delete your documents as needed. Keep your knowledge base 
                  up-to-date and well-maintained.
                </p>
                <Link to="/documents" className="btn btn-light mt-3">
                  Manage Documents <FontAwesomeIcon icon={faArrowRight} className="ms-2" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Benefits Section */}
      <div className="container mb-5">
        <div className="row align-items-center">
          <div className="col-lg-6 mb-4 mb-lg-0">
            <h2 className="mb-4">Why Use Our PDF Knowledge Base?</h2>
            <div className="benefit-item d-flex align-items-start mb-4">
              <div className="benefit-icon me-3">
                <FontAwesomeIcon icon={faRocket} className="text-primary fs-3" />
              </div>
              <div>
                <h4>Fast and Efficient</h4>
                <p className="text-muted">
                  Our advanced indexing system ensures quick search results, saving you valuable time.
                </p>
              </div>
            </div>
            <div className="benefit-item d-flex align-items-start mb-4">
              <div className="benefit-icon me-3">
                <FontAwesomeIcon icon={faLightbulb} className="text-primary fs-3" />
              </div>
              <div>
                <h4>Smart Search</h4>
                <p className="text-muted">
                  Intelligent search algorithms understand context and provide the most relevant results.
                </p>
              </div>
            </div>
            <div className="benefit-item d-flex align-items-start">
              <div className="benefit-icon me-3">
                <FontAwesomeIcon icon={faBookReader} className="text-primary fs-3" />
              </div>
              <div>
                <h4>Centralized Knowledge</h4>
                <p className="text-muted">
                  Keep all your important documents in one place, accessible whenever you need them.
                </p>
              </div>
            </div>
          </div>
          <div className="col-lg-6">
            <div className="card border-0 shadow-lg">
              <div className="card-body p-0">
                <img 
                  src="/images/knowledge-base-illustration.svg" 
                  alt="Knowledge Base Illustration" 
                  className="img-fluid rounded"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = "/images/placeholder.svg";
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Call to Action section removed */}
    </div>
  );
};

export default Home;
