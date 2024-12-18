import React, { useEffect, useState } from 'react';
import {
  AppLayout,
  BreadcrumbGroup,
  Container,
  ContentLayout,
  Flashbar,
  Header,
  SideNavigation,
  Table,
  Box,
} from '@cloudscape-design/components';
import { I18nProvider } from '@cloudscape-design/components/i18n';
import messages from '@cloudscape-design/components/i18n/messages/all.en';
import './AppLayoutPreview.css';

const LOCALE = 'en';
const API_URL = 'https://9mehg9f4y9.execute-api.ap-southeast-1.amazonaws.com/dev/';

export default function AppLayoutPreview() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [navigationOpen, setNavigationOpen] = useState(true);
  const [selectedItemId, setSelectedItemId] = useState(0); // Set giá trị mặc định là 0

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(API_URL);
        const result = await response.json();
        const bodyData = JSON.parse(result.body);
        
        if (bodyData.success && bodyData.data) {
          setData(bodyData.data);
          if (bodyData.data.length > 0) {
            setSelectedItemId(0);
          }
        } else {
          setError('No data available');
        }
      } catch (err) {
        console.error('Fetch error:', err);
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Debug useEffect
  useEffect(() => {
    if (selectedItemId !== null && data) {
      console.log('Selected item:', data[selectedItemId]);
    }
  }, [selectedItemId, data]);

  const LoadingSpinner = () => (
    <div className="loading-container">
      <div className="loading-spinner"></div>
      <div className="loading-text">Loading analysis data...</div>
    </div>
  );

  const NoDataMessage = () => (
    <div className="no-data-container">
      <div className="no-data-icon">📈</div>
      <h3>No Analysis Data Available</h3>
      <p>There are currently no analysis results to display.</p>
    </div>
  );

  const navigationItems = React.useMemo(() => {
    if (!data) return [];
    
    return data.map((item, index) => ({
      type: 'link',
      text: item.ContactId,
      href: `${index}`, // Sửa lại string template
      selected: selectedItemId === index,
      onItemClick: (e) => {
        e.preventDefault();
        console.log('Clicking item:', index); // Debug log
        setSelectedItemId(index);
      }
    }));
  }, [data, selectedItemId]);

  useEffect(() => {
    if (selectedItemId !== null && data) {
      console.log('Selected item:', data[selectedItemId]);
    }
  }, [selectedItemId, data]);

  const renderSelectedItem = () => {
    if (!data || selectedItemId === null) return null;
    
    const item = data[selectedItemId];
    return (
      <>
      <Container
        header={
          <Header
            variant="h2"
            className="section-header"
            description={
              <div className="header-description">
                <span className="timestamp">🕒 {new Date(item.AnalysisTimestamp.replace(' ', 'T')).toLocaleString()}</span>
                <span className="file-info">📁 {item.ContactId}</span>
                <span className="phone-info">📞 {item.PhoneNumber}</span>
              </div>
            }
          >
            Call Analysis Report
          </Header>
        }
      >
        <div className="container-content">
          <div className="dashboard-grid">
            <div className="score-card">
              <div className="score-header">Compliance Score</div>
              <div className="score-value">{item.Analysis.compliance_score}</div>
              <div className="score-status">
                {item.Analysis.compliance_score >= 7 ? '✅ Good' : '⚠️ Needs Improvement'}
              </div>
            </div>
  
            <div className="summary-cards">
              <div className="summary-card violations">
                <div className="card-icon">⚠️</div>
                <div className="card-title">Violations Found</div>
                <div className="card-value">{item.Analysis.violations.length}</div>
              </div>
              <div className="summary-card recommendations">
                <div className="card-icon">💡</div>
                <div className="card-title">Recommendations</div>
                <div className="card-value">{item.Analysis.recommendations.length}</div>
              </div>
            </div>
          </div>
  
          <div className="analysis-container">
            <div className="analysis-section violations">
              <h4><span className="section-icon">⚠️</span> Violations Detected</h4>
              <ul className="analysis-list">
                {item.Analysis.violations.map((violation, idx) => (
                  <li key={idx} className="violation-item">
                    <span className="item-number">{idx + 1}</span>
                    {violation}
                  </li>
                ))}
              </ul>
            </div>
  
            <div className="analysis-section recommendations">
              <h4><span className="section-icon">💡</span> Improvement Recommendations</h4>
              <ul className="analysis-list">
                {item.Analysis.recommendations.map((rec, idx) => (
                  <li key={idx} className="recommendation-item">
                    <span className="item-number">{idx + 1}</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          </div>
  
          <div className="detailed-analysis">
            <h4><span className="section-icon">📋</span> Detailed Analysis</h4>
            <div className="analysis-content">
              {item.Analysis.detailed_analysis}
            </div>
          </div>
  
          <div className="emotion-grid">
            <div className="emotion-card customer">
              <h4><span className="section-icon"></span> Customer Emotion</h4>
              <div className="emotion-content">
                {item.Analysis.customer_emotion}
              </div>
            </div>
            <div className="emotion-card details">
              <h4><span className="section-icon">📊</span> Emotion Analysis</h4>
              <div className="emotion-content">
                {item.Analysis.emotion_details}
              </div>
            </div>
          </div>
        </div>
      </Container>
      <Container
        header={
          <Header
            variant="h2"
            description="Select an analysis result to view details"
          >
            Analysis History
          </Header>
        }
      >
        <Table
          columnDefinitions={[
            {
              id: 'fileName',
              header: 'ContactId',
              cell: item => item.ContactId ,
              sortingField: 'ContactId'
            },
            {
              id: 'phoneNumber',  // Thêm cột mới
              header: 'Phone Number',
              cell: item => item.PhoneNumber,
              sortingField: 'PhoneNumber'
            },
            {
              id: 'timestamp',
              header: 'Timestamp',
              cell: item => new Date(item.AnalysisTimestamp.replace(' ', 'T')).toLocaleString(),
              sortingField: 'Timestamp'
            },
            {
              id: 'score',
              header: 'Compliance Score',
              cell: item => (
                <Box textAlign="center" margin={{ horizontal: "xxxl" }} color={item.Analysis.compliance_score >= 7 ? "text-status-success" : "text-status-error"}>
                  {item.Analysis.compliance_score}
                </Box>
              )
            }
          ]}
          items={data}
          selectedItems={[data[selectedItemId]]}
          selectionType="single"
          onSelectionChange={({ detail }) => {
            const selectedIndex = data.findIndex(item => item === detail.selectedItems[0]);
            if (selectedIndex !== -1) {
              setSelectedItemId(selectedIndex);
            }
          }}
          variant="container"
          stickyHeader
          stripedRows
          wrapLines={false}
        />
      </Container>
      
      </>
      
    );
  };

  return (
    <I18nProvider locale={LOCALE} messages={[messages]}>
      <AppLayout
        breadcrumbs={
          <BreadcrumbGroup
            items={[
              { text: 'Home', href: '#' },
              { text: 'Analysis Results', href: '#' },
            ]}
          />
        }
        navigationOpen={navigationOpen}
        onNavigationChange={({ detail }) => setNavigationOpen(detail.open)}
        navigation={
          <SideNavigation
            header={{
              href: '#',
              text: 'Call Analysis',
            }}
            items={navigationItems}
            activeHref={`${selectedItemId}`}
            onNavigationChange={({ detail }) => {
              console.log('Navigation changed:', detail);
            }}
          />
        }
        notifications={
          error && (
            <Flashbar
              items={[
                {
                  type: 'error',
                  content: `Error: ${error}`,
                  dismissible: true,
                  id: 'error_message',
                },
              ]}
            />
          )
        }
        content={
          <ContentLayout
            header={
              <Header variant="h1">
                Call Analysis Results
              </Header>
            }
          >
            <Container>
              {isLoading ? (
                <LoadingSpinner />
              ) : error ? (
                <div className="error-container">
                  <div className="error-icon">⚠️</div>
                  <h3>Error Loading Data</h3>
                  <p>{error}</p>
                </div>
              ) : !data || data.length === 0 ? (
                <NoDataMessage />
              ) : (
                renderSelectedItem()
              )}
            </Container>
          </ContentLayout>
        }
      />
    </I18nProvider>
  );
}