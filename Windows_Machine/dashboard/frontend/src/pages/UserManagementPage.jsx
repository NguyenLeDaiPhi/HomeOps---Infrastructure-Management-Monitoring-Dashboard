import React, { useState, useEffect, useCallback } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { SectionCard } from '../components/layout/SectionCard';
import { StatusBadge } from '../components/shared/StatusBadge';
import { authFetch, AUTH_API_BASE } from '../auth/api';
import { useAuth } from '../auth/AuthContext';

export function UserManagementPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Modal state for Create User
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newRole, setNewRole] = useState('viewer');
  const [creating, setCreating] = useState(false);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await authFetch(`${AUTH_API_BASE}/users`);
      if (res.ok) {
        const data = await res.json();
        setUsers(data || []);
      } else {
        const errData = await res.json();
        setError(errData.detail || 'Failed to load users.');
      }
    } catch (err) {
      setError(`Network error loading users: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setCreating(true);

    try {
      const res = await authFetch(`${AUTH_API_BASE}/users`, {
        method: 'POST',
        body: JSON.stringify({
          username: newUsername.trim(),
          password: newPassword,
          role: newRole,
          full_name: newFullName.trim() || undefined,
          email: newEmail.trim() || undefined,
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setSuccessMsg(`User '${data.username}' created successfully with role '${data.role.toUpperCase()}'.`);
        setShowCreateModal(false);
        setNewUsername('');
        setNewPassword('');
        setNewFullName('');
        setNewEmail('');
        setNewRole('viewer');
        fetchUsers();
      } else {
        setError(data.detail || 'Failed to create user.');
      }
    } catch (err) {
      setError(`Error creating user: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  const handleToggleActive = async (targetUser) => {
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await authFetch(`${AUTH_API_BASE}/users/${targetUser.id}`, {
        method: 'PUT',
        body: JSON.stringify({ is_active: !targetUser.is_active }),
      });
      if (res.ok) {
        const updated = await res.json();
        setSuccessMsg(`User '${updated.username}' status set to ${updated.is_active ? 'ACTIVE' : 'DEACTIVATED'}.`);
        fetchUsers();
      } else {
        const errData = await res.json();
        setError(errData.detail || 'Failed to update user status.');
      }
    } catch (err) {
      setError(`Error updating user status: ${err.message}`);
    }
  };

  const handleChangeRole = async (targetUser, roleValue) => {
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await authFetch(`${AUTH_API_BASE}/users/${targetUser.id}`, {
        method: 'PUT',
        body: JSON.stringify({ role: roleValue }),
      });
      if (res.ok) {
        const updated = await res.json();
        setSuccessMsg(`User '${updated.username}' role updated to '${updated.role.toUpperCase()}'.`);
        fetchUsers();
      } else {
        const errData = await res.json();
        setError(errData.detail || 'Failed to update role.');
      }
    } catch (err) {
      setError(`Error updating user role: ${err.message}`);
    }
  };

  const handleDeleteUser = async (targetUser) => {
    if (!window.confirm(`Are you sure you want to delete user '${targetUser.username}'?`)) return;
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await authFetch(`${AUTH_API_BASE}/users/${targetUser.id}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        setSuccessMsg(`User '${targetUser.username}' deleted successfully.`);
        fetchUsers();
      } else {
        const errData = await res.json();
        setError(errData.detail || 'Failed to delete user.');
      }
    } catch (err) {
      setError(`Error deleting user: ${err.message}`);
    }
  };

  return (
    <PageContainer
      title="User Accounts & RBAC Authorization"
      subtitle="Manage HomeOps system accounts, assign access roles (Admin, Operator, Viewer), and manage security status."
      icon="👥"
      actions={
        <button
          className="btn btn-primary text-xs"
          onClick={() => setShowCreateModal(true)}
        >
          + Create New Account
        </button>
      }
    >
      {error && (
        <div className="action-error-banner margin-bottom-4">
          <span>⚠️ {error}</span>
        </div>
      )}

      {successMsg && (
        <div className="action-success-banner margin-bottom-4">
          <span>✅ {successMsg}</span>
        </div>
      )}

      <SectionCard
        title="Registered System Users"
        subtitle={`${users.length} total user accounts configured in PostgreSQL`}
        icon="🛡️"
      >
        <div className="table-responsive">
          <table className="proc-table" id="users-management-table">
            <thead>
              <tr>
                <th>USERNAME</th>
                <th>FULL NAME</th>
                <th>ROLE</th>
                <th>STATUS</th>
                <th>LAST LOGIN</th>
                <th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className="empty-state">
                    Loading registered user accounts...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan="6" className="empty-state">
                    No user accounts found.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id}>
                    <td className="font-semibold text-main">
                      <span className="font-mono text-cyan">{u.username}</span>
                      {currentUser?.id === u.id && (
                        <span className="text-dim text-xs margin-left-2">(You)</span>
                      )}
                    </td>
                    <td className="text-xs">{u.full_name || '—'}</td>
                    <td>
                      <select
                        className="tail-select text-xs font-semibold"
                        value={u.role}
                        disabled={u.id === currentUser?.id}
                        onChange={(e) => handleChangeRole(u, e.target.value)}
                      >
                        <option value="admin">ADMIN</option>
                        <option value="operator">OPERATOR</option>
                        <option value="viewer">VIEWER</option>
                      </select>
                    </td>
                    <td>
                      <StatusBadge
                        status={u.is_active ? 'ACTIVE' : 'DEACTIVATED'}
                        type={u.is_active ? 'active' : 'idle'}
                      />
                    </td>
                    <td className="font-mono text-xs text-muted">
                      {u.last_login ? new Date(u.last_login).toLocaleString() : 'Never'}
                    </td>
                    <td>
                      <div className="flex-row gap-2">
                        <button
                          className={`btn ${u.is_active ? 'btn-secondary' : 'btn-primary'} text-xs`}
                          disabled={u.id === currentUser?.id}
                          onClick={() => handleToggleActive(u)}
                        >
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button
                          className="btn btn-secondary text-xs text-warning"
                          disabled={u.id === currentUser?.id}
                          onClick={() => handleDeleteUser(u)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </SectionCard>

      {/* Modal for Creating User */}
      {showCreateModal && (
        <div className="logs-modal-overlay">
          <div className="logs-modal-card max-w-lg">
            <div className="logs-modal-header space-between">
              <h3>Create User Account</h3>
              <button
                className="banner-close"
                onClick={() => setShowCreateModal(false)}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleCreateUser} className="margin-top-4 flex-col gap-3">
              <div className="form-group">
                <label className="input-label">USERNAME *</label>
                <input
                  type="text"
                  className="login-input font-mono"
                  placeholder="e.g. operator_alice"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="input-label">PASSWORD *</label>
                <input
                  type="password"
                  className="login-input font-mono"
                  placeholder="Minimum 6 characters"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="input-label">ROLE *</label>
                <select
                  className="tail-select full-width-select"
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                >
                  <option value="viewer">VIEWER — Read-only telemetry access</option>
                  <option value="operator">OPERATOR — Dashboard + Docker container control</option>
                  <option value="admin">ADMIN — Full system & User management access</option>
                </select>
              </div>

              <div className="form-group">
                <label className="input-label">FULL NAME</label>
                <input
                  type="text"
                  className="login-input"
                  placeholder="e.g. Alice Smith"
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="input-label">EMAIL</label>
                <input
                  type="email"
                  className="login-input"
                  placeholder="e.g. alice@homeops.local"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                />
              </div>

              <div className="flex-row space-between margin-top-4">
                <button
                  type="button"
                  className="btn btn-secondary text-xs"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary text-xs"
                  disabled={creating}
                >
                  {creating ? 'Creating Account...' : 'Create Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </PageContainer>
  );
}
