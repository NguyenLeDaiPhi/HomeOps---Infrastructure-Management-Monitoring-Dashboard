import React from 'react';

export function DataTable({ headers, children, className = '' }) {
  return (
    <div className={`table-responsive ${className}`}>
      <table className="proc-table">
        <thead>
          <tr>
            {headers.map((header, idx) => (
              <th key={idx}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
