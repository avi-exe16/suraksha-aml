import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const ShapChart = ({ explanation }) => {
    if (!explanation || explanation.length === 0) {
        return <p style={{ color: '#6b7280', fontSize: '14px' }}>No explanation data available.</p>;
    }

    const data = explanation.map((item) => ({
        feature: item.feature.replace(/_/g, ' '),
        importance: parseFloat((item.importance * 100).toFixed(2)),
        value: item.value,
    }));

    const getBarColor = (importance) => {
        if (importance >= 40) return '#ef4444';
        if (importance >= 20) return '#f59e0b';
        return '#3b82f6';
    };

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const item = payload[0].payload;
            return (
                <div style={{
                    background: '#1f2937',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '10px 14px',
                    color: '#f9fafb',
                    fontSize: '13px',
                }}>
                    <p style={{ margin: '0 0 4px 0', fontWeight: '600' }}>{item.feature}</p>
                    <p style={{ margin: '0 0 2px 0' }}>Importance: {item.importance}%</p>
                    <p style={{ margin: '0' }}>Value: {item.value}</p>
                </div>
            );
        }
        return null;
    };

    return (
        <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart
                    data={data}
                    layout="vertical"
                    margin={{ top: 4, right: 24, left: 120, bottom: 4 }}
                >
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" horizontal={false} />
                    <XAxis
                        type="number"
                        tick={{ fontSize: 12, fill: '#6b7280' }}
                        tickFormatter={(v) => `${v}%`}
                    />
                    <YAxis
                        type="category"
                        dataKey="feature"
                        tick={{ fontSize: 12, fill: '#374151' }}
                        width={115}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                        {data.map((entry, index) => (
                            <Cell key={index} fill={getBarColor(entry.importance)} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};

export default ShapChart;