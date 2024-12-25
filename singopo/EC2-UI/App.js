import React, { useEffect, useState, useMemo } from 'react';
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
  Tabs,
  CollectionPreferences,
  TextFilter
} from '@cloudscape-design/components';
import { I18nProvider } from '@cloudscape-design/components/i18n';
import messages from '@cloudscape-design/components/i18n/messages/all.en';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Styles
import './AppLayoutPreview.css';

// Constants
const LOCALE = 'en';
const API_URL = 'https://9mehg9f4y9.execute-api.ap-southeast-1.amazonaws.com/dev/';
const CUSTOMER_API_URL = 'https://r1y81iqs4c.execute-api.ap-southeast-1.amazonaws.com/dev/';

// Thành phần thống kê tổng hợp
const AnalyticsSummary = ({ data }) => {
  const summary = useMemo(() => {
    if (!data || !data.length) return null;

    // Chuyển đổi điểm sang số và tính trung bình
    const validScores = data
      .filter(item => item?.Analysis?.compliance_score != null)
      .map(item => Number(item.Analysis.compliance_score));

    console.log('Valid scores:', validScores);

    const sum = validScores.reduce((acc, score) => acc + score, 0);
    console.log('Sum:', sum);

    const avgCompliance = sum / validScores.length;
    console.log('Average:', avgCompliance);

    // Đếm số cuộc gọi
    const totalCalls = data.length;

    // Thống kê cảm xúc
    const emotionCounts = data.reduce((acc, item) => {
      const emotion = item.Analysis.customer_emotion;
      acc[emotion] = (acc[emotion] || 0) + 1;
      return acc;
    }, {});

    const mostCommonEmotion = Object.entries(emotionCounts)
      .sort(([,a], [,b]) => b - a)[0][0];

    return {
      avgCompliance: avgCompliance.toFixed(2),
      totalCalls,
      mostCommonEmotion
    };
  }, [data]);

  if (!summary) return null;

  const getEmotionColor = (emotion) => {
    // Định nghĩa các cảm xúc và màu tương ứng
    const emotionTypes = {
      // Tích cực
      'tích cực': '#00C49F',
      'satisfied': '#00C49F',
      'positive': '#00C49F',
      
      // Trung tính
      'trung tính': '#9E9E9E',
      'calm': '#9E9E9E',
      'normal': '#9E9E9E',
      
      // Tiêu cực
      'tiêu cực': '#FF4D4D',
      'frustrated': '#FF4D4D',
      'negative': '#FF4D4D',
      'unsatisfied': '#FF4D4D'
    };
  
    return emotionTypes[emotion.toLowerCase()] || '#9E9E9E';
  };
  
  return (
    <Box padding="l" className="summary-container">
      <div className="summary-grid">
        <div className="summary-item">
          <div className="summary-label">Điểm Compliance Trung bình</div>
          <div className="summary-value">{summary.avgCompliance}</div>
        </div>
        <div className="summary-item">
          <div className="summary-label">Tổng số cuộc gọi</div>
          <div className="summary-value">{summary.totalCalls}</div>
        </div>
        <div className="summary-item">
  <div className="summary-label">Cảm xúc phổ biến nhất</div>
  <div 
    className="summary-value"
    style={{ color: getEmotionColor(summary.mostCommonEmotion) }}
  >
    {summary.mostCommonEmotion}
  </div>
</div>
      </div>
    </Box>
  );
};

// Biểu đồ tròn cảm xúc
const EmotionPieChart = ({ data }) => {
  const emotionData = useMemo(() => {
    if (!data || !data.length) return [];
    
    const emotionCounts = data.reduce((acc, item) => {
      const emotion = item.Analysis.customer_emotion;
      acc[emotion] = (acc[emotion] || 0) + 1;
      return acc;
    }, {});

    return Object.entries(emotionCounts).map(([name, value]) => ({
      name,
      value
    }));
  }, [data]);

  // Màu sắc theo loại cảm xúc
  const getEmotionColor = (emotion) => {
    const emotionColors = {
      'tích cực': '#00C49F',    // Xanh lá
      'trung tính': '#9E9E9E',  // Xám
      'tiêu cực': '#FF7043'     // Đỏ
    };
    return emotionColors[emotion.toLowerCase()] || '#8884d8';
  };

  return (
    <Box padding="l">
      <h3 className="chart-title">Phân bố cảm xúc khách hàng</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={emotionData}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          >
            {emotionData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={getEmotionColor(entry.name)}
              />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </Box>
  );
};

// Biểu đồ cột điểm compliance
const ComplianceBarChart = ({ data }) => {
  const complianceData = useMemo(() => {
    if (!data || !data.length) return [];

    // Tạo các khoảng điểm với màu sắc tương ứng
    const ranges = [
      { range: '0-2', min: 0, max: 1.99, color: '#FF4D4D' },    // Đỏ đậm
      { range: '2-4', min: 2, max: 3.99, color: '#FF7043' },    // Đỏ cam
      { range: '4-6', min: 4, max: 5.99, color: '#9E9E9E' },    // Xám (trung bình)
      { range: '6-8', min: 6, max: 7.99, color: '#81C784' },    // Xanh lá nhạt
      { range: '8-10', min: 8, max: 10, color: '#00C49F' }      // Xanh lá đậm
    ];

    // Đếm số lượng trong mỗi khoảng
    const distribution = ranges.map(range => ({
      name: range.range,
      count: data.filter(item => 
        item.Analysis.compliance_score >= range.min && 
        item.Analysis.compliance_score <= range.max
      ).length,
      color: range.color  // Thêm màu vào dữ liệu
    }));

    return distribution;
  }, [data]);

  return (
    <Box padding="l">
      <h3 className="chart-title">Phân bố điểm Compliance</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={complianceData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar 
            dataKey="count" 
            name="Số lượng cuộc gọi"
          >
            {complianceData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`}
                fill={entry.color}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
};
// Thêm component Analytics Dashboard
const AnalyticsDashboard = ({ data }) => {
  if (!data) return <NoDataMessage />;

  return (
    <Container>
      <div className="analytics-container">
        {/* Statistical Summary */}
        <AnalyticsSummary data={data} />
        
        {/* Charts */}
        <div className="charts-grid">
          <EmotionPieChart data={data} />
          <ComplianceBarChart data={data} />
        </div>
      </div>
    </Container>
  );
};

// Dashboard Analytics Container
// Reusable Components
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

// Custom Hooks
const useAnalysisData = (url) => {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(url);
        const result = await response.json();
        const analysisData = JSON.parse(result.body);
        if (analysisData.success && analysisData.data) {
          setData(analysisData.data);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [url]);

  return { data, isLoading, error };
};

const useCustomerData = (url) => {
  const [customerData, setCustomerData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(url);
        const result = await response.json();
        const customers = JSON.parse(result.body);
        setCustomerData(customers);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [url]);

  return { customerData, isLoading, error };
};

const CustomerListContainer = ({ customerData, isLoading }) => {
  const [selectedItems, setSelectedItems] = useState([]);
  const [sortingColumn, setSortingColumn] = useState({ sortingField: "CustomerId", sortingDescending: false });

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <Container
      header={
        <Header
          variant="h2"
          description={`Total Customers: ${customerData?.length || 0}`}
          counter={`(${selectedItems.length}/${customerData?.length || 0})`}
        >
          Customer Information
        </Header>
      }
    >
      <Table
        columnDefinitions={[
          {
            id: 'customerId',
            header: 'Customer ID',
            cell: item => (
              <Box color="text-status-info" fontWeight="bold">
                {item.CustomerId}
              </Box>
            ),
            sortingField: 'CustomerId',
            width: 120
          },
          {
            id: 'name',
            header: 'Full Name',
            cell: item => (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>

                <div>
                  <Box>
                    {`${item.FirstName} ${item.MiddleName} ${item.LastName}`}
                  </Box>
                </div>
              </div>
            ),
            sortingField: 'FirstName',
            width: 250
          },
          {
            id: 'contact',
            header: 'Contact Information',
            cell: item => (
              <div>
                <Box fontSize="body-m">
                  📱 {item.PhoneNumber}
                </Box>
                <Box color="text-status-info" fontSize="body-s">
                  ✉️ {item.PersonalEmail || item.BusinessEmail || 'N/A'}
                </Box>
              </div>
            ),
            width: 250
          },
          {
            id: 'address',
            header: 'Location',
            cell: item => (
              <div>
                <Box fontWeight="normal">
                  🏠 {item.StreetAddress}
                </Box>
                <Box color="text-status-inactive" fontSize="body-s">
                  📍 {`${item.City}, ${item.Country}`}
                </Box>
              </div>
            ),
            sortingField: 'City'
          },
          {
            id: 'type',
            header: 'Customer Type',
            cell: item => (
              <Box
                backgroundColor={item.PartyType === 'Business' ? 'blue-100' : 'green-100'}
                color={item.PartyType === 'Business' ? 'blue-600' : 'green-600'}
                padding="xs"
                borderRadius="rounded"
                textAlign="center"
                fontSize="body-s"
                fontWeight="bold"
              >
                {item.PartyType}
              </Box>
            ),
            sortingField: 'PartyType',
            width: 130
          }
        ]}
        items={customerData || []}
        loading={isLoading}
        loadingText="Loading customers..."
        selectionType="multi"
        selectedItems={selectedItems}
        onSelectionChange={({ detail }) => setSelectedItems(detail.selectedItems)}
        sortingColumn={sortingColumn}
        onSortingChange={({ detail }) => setSortingColumn(detail)}
        variant="container"
        stickyHeader
        stripedRows
        wrapLines={false}
        filter={
          <TextFilter
            filteringPlaceholder="Find customers"
            filteringText=""
          />
        }
        preferences={
          <CollectionPreferences
            title="Preferences"
            confirmLabel="Confirm"
            cancelLabel="Cancel"
            preferences={{
              pageSize: 10,
              visibleContent: ['customerId', 'name', 'contact', 'address', 'type', 'status']
            }}
          />
        }
      />
    </Container>
  );
};


// Main Component
export default function CallAnalysisDashboard() {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState(0);
  const [activeTab, setActiveTab] = useState('analysis');

  const { data, isLoading: analysisLoading, error: analysisError } = useAnalysisData(API_URL);
  const { customerData, isLoading: customerLoading, error: customerError } = useCustomerData(CUSTOMER_API_URL);

  const error = analysisError || customerError;
  const isLoading = analysisLoading || customerLoading;

  const navigationItems = useMemo(() => {
    if (!data) return [];
    return data.map((item, index) => ({
      type: 'link',
      text: item.ContactId,
      href: `${index}`,
      selected: selectedItemId === index,
      onItemClick: (e) => {
        e.preventDefault();
        setSelectedItemId(index);
      }
    }));
  }, [data, selectedItemId]);

  // Thêm state để theo dõi trạng thái sắp xếp
const [sortingColumn, setSortingColumn] = useState({ sortingField: "Timestamp", sortingDescending: true });

// Hàm sắp xếp dữ liệu
const getSortedItems = (items, column, descending) => {
  if (!column) return items;

  return [...items].sort((a, b) => {
    let valueA, valueB;
    
    // Xử lý các trường hợp đặc biệt
    if (column === 'Timestamp') {
      valueA = new Date(a.AnalysisTimestamp.replace(' ', 'T')).getTime();
      valueB = new Date(b.AnalysisTimestamp.replace(' ', 'T')).getTime();
    } else if (column === 'Name') {
      valueA = `\${a.CustomerInfo?.FirstName || ''} \${a.CustomerInfo?.MiddleName || ''} \${a.CustomerInfo?.LastName || ''}`.trim();
      valueB = `\${b.CustomerInfo?.FirstName || ''} \${b.CustomerInfo?.MiddleName || ''} \${b.CustomerInfo?.LastName || ''}`.trim();
    } else {
      valueA = a[column];
      valueB = b[column];
    }

    // So sánh
    if (valueA < valueB) return descending ? 1 : -1;
    if (valueA > valueB) return descending ? -1 : 1;
    return 0;
  });
};
  const renderSelectedItem = () => {
    if (!data || selectedItemId === null) return null;
    
    const item = data[selectedItemId];
    return (
      <>
        {/* Analysis Details Container */}
        <Container
  header={
      <Header
        variant="h2"
        description={
          <div className="header-description">
            <div className="info-row">
              <span className="timestamp">⏱ {new Date(item.AnalysisTimestamp.replace(' ', 'T')).toLocaleString()}</span>
              <span className="file-info">📁 {item.ContactId}</span>
              <span className="phone-info">📞 {item.PhoneNumber}</span>
            </div>
            <div className="customer-info-row">
              <span className="customer-id">
                👤 Customer ID:   {item.CustomerInfo?.CustomerId}
              </span>
              <span className="customer-name">
                📝 Name: {`${item.CustomerInfo?.FirstName} ${item.CustomerInfo?.MiddleName} ${item.CustomerInfo?.LastName}`}
              </span>
              <span className="customer-type">
                Type: {item.CustomerInfo?.PartyType}
              </span>
              <span className="customer-email">
                ✉️ Email: {item.CustomerInfo?.Email || 'N/A'}
              </span>
              <span className="customer-address">
                🏠 Address: {`${item.CustomerInfo?.Address?.Street}, ${item.CustomerInfo?.Address?.City}`}
              </span>
            </div>
          </div>
        }
      >
        Call Analysis Report
      </Header>
        }
      >
          {/* Analysis Content */}
          <div className="container-content">
            {/* Score and Summary Cards */}
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

            {/* Analysis Details */}
            <div className="analysis-container">
              {/* Violations */}
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

              {/* Recommendations */}
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

            {/* Detailed Analysis */}
            <div className="detailed-analysis">
              <h4><span className="section-icon">📋</span> Detailed Analysis</h4>
              <div className="analysis-content">
                {item.Analysis.detailed_analysis}
              </div>
            </div>

            {/* Emotion Analysis */}
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

        {/* Analysis History Table */}
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
                cell: item => item.ContactId,
                sortingField: 'ContactId'
              },
              {
                id: 'Name',
                header: 'Name',
                cell: item => item.CustomerInfo?.FirstName+" " +item.CustomerInfo?.MiddleName+" " +item.CustomerInfo?.LastName,
                sortingField: 'Name'
              },
              {
                id: 'phoneNumber',
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
                  <Box 
                    textAlign="center" 
                    margin={{ horizontal: "xxxl" }} 
                    color={item.Analysis.compliance_score >= 7 ? "text-status-success" : "text-status-error"}
                  >
                    {item.Analysis.compliance_score}
                  </Box>
                ),
                sortingField: 'score'
              }
            ]}
            items={getSortedItems(data, sortingColumn.sortingField, sortingColumn.sortingDescending)}
            selectedItems={[data[selectedItemId]]}
            selectionType="single"
            onSelectionChange={({ detail }) => {
              const selectedIndex = data.findIndex(item => item === detail.selectedItems[0]);
              if (selectedIndex !== -1) {
                setSelectedItemId(selectedIndex);
              }
            }}
            sortingColumn={sortingColumn}
            onSortingChange={({ detail }) => setSortingColumn(detail)}
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
                <Tabs
                  activeTabId={activeTab}
                  onChange={({ detail }) => setActiveTab(detail.activeTabId)}
                  tabs={[
                    {
                      label: "Call Analysis",
                      id: "analysis",
                      content: renderSelectedItem()
                    },
                    {
                      label: "Customer Information",
                      id: "customerList",
                      content: (
                        <CustomerListContainer 
                          customerData={customerData}
                          isLoading={customerLoading}
                        />
                      )
                    },
                    {
                      label: "Analytics Dashboard",
                      id: "analytics",
                      content: <AnalyticsDashboard data={data} />
                    }
                  ]}
                />
              )}
            </Container>
          </ContentLayout>
        }
      />
    </I18nProvider>
  );
}