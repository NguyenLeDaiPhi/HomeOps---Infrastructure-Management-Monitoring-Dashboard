import React from 'react';

export function SearchBar({ value, onChange, placeholder = 'Search...', className = '' }) {
  return (
    <div className={`search-box ${className}`}>
      <span className="search-icon">🔍</span>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      {value && (
        <button className="search-clear-btn" onClick={() => onChange('')} title="Clear search">
          ✕
        </button>
      )}
    </div>
  );
}
