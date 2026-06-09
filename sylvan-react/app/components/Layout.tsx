import React from 'react';
import TopBar from './TopBar';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="main-layout">
      <TopBar />
      <div className="body-content">
        <div className="main-content">{children}</div>
      </div>
      <p style={{ color: '#999', padding: '10px', textAlign: 'center' }}>
        Wizards of the Coast, Magic: The Gathering, and their logos are trademarks
        of Wizards of the Coast LLC. © 1995-{new Date().getFullYear()} Wizards. All
        rights reserved.
      </p>
    </div>
  );
}
