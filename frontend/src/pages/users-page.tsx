import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'

import { ConfirmButton } from '@/components/common/confirm-button'
import { EmptyState } from '@/components/common/empty-state'
import { ErrorState } from '@/components/common/error-state'
import { LoadingState } from '@/components/common/loading-state'
import { PageShell } from '@/components/common/page-shell'
import { StatusBadge } from '@/components/common/status-badge'
import { TableCard, tableClassName, tdClassName, thClassName } from '@/components/common/table'
import { getApiErrorMessage } from '@/services/api-client'
import { userService } from '@/services/user-service'
import type { RoleName } from '@/types/user'

const inputClassName =
  'rounded-xl border border-slate-400/30 bg-slate-950/60 px-3 py-2.5 text-slate-50 outline-none focus:border-sky-400 focus:ring-4 focus:ring-sky-400/15'
const buttonClassName =
  'min-h-10 rounded-xl bg-gradient-to-br from-sky-400 to-green-400 px-4 font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-60'
const dangerButtonClassName =
  'min-h-10 rounded-xl bg-red-400 px-4 font-bold text-red-950 disabled:cursor-not-allowed disabled:opacity-60'

export function UsersPage() {
  const queryClient = useQueryClient()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const usersQuery = useQuery({
    queryKey: ['users'],
    queryFn: () => userService.list({ limit: 100 }),
  })

  const createUserMutation = useMutation({
    mutationFn: userService.create,
    onSuccess: async () => {
      setEmail('')
      setPassword('')
      await queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  const assignRoleMutation = useMutation({
    mutationFn: ({ userId, roleName }: { userId: number; roleName: RoleName }) =>
      userService.assignRole(userId, roleName),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  const deleteUserMutation = useMutation({
    mutationFn: userService.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  async function handleCreateUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)

    if (!email.includes('@')) {
      setFormError('Enter a valid email address.')
      return
    }

    if (password.length < 8) {
      setFormError('Password must be at least 8 characters.')
      return
    }

    await createUserMutation.mutateAsync({ email, password })
  }

  return (
    <PageShell
      description="Create users, review MFA status, and assign dashboard roles."
      eyebrow="Admin"
      title="Users"
    >
      <form
        className="grid grid-cols-[1fr_1fr_auto] gap-3 rounded-3xl border border-slate-400/20 bg-slate-900/80 p-5 shadow-2xl shadow-black/30 backdrop-blur-xl max-lg:grid-cols-1"
        onSubmit={handleCreateUser}
      >
        <input
          className={inputClassName}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="user@example.com"
          required
          type="email"
          value={email}
        />
        <input
          className={inputClassName}
          minLength={8}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Temporary password"
          required
          type="password"
          value={password}
        />
        <button className={buttonClassName} disabled={createUserMutation.isPending} type="submit">
          {createUserMutation.isPending ? 'Creating...' : 'Create user'}
        </button>
      </form>

      {formError && <ErrorState title="Invalid user details" message={formError} />}
      {createUserMutation.isError && <ErrorState message={getApiErrorMessage(createUserMutation.error)} />}
      {assignRoleMutation.isError && <ErrorState message={getApiErrorMessage(assignRoleMutation.error)} />}
      {deleteUserMutation.isError && <ErrorState message={getApiErrorMessage(deleteUserMutation.error)} />}

      {usersQuery.isLoading && <LoadingState message="Loading users..." />}
      {usersQuery.isError && <ErrorState message={getApiErrorMessage(usersQuery.error)} />}

      {usersQuery.data?.users.length === 0 && (
        <EmptyState title="No users found" message="Create the first user with the form above." />
      )}

      {usersQuery.data && usersQuery.data.users.length > 0 && (
        <TableCard>
          <table className={tableClassName}>
            <thead>
              <tr>
                <th className={thClassName}>User</th>
                <th className={thClassName}>Status</th>
                <th className={thClassName}>MFA</th>
                <th className={thClassName}>Roles</th>
                <th className={thClassName}>Assign role</th>
                <th className={thClassName}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {usersQuery.data.users.map((user) => (
                <tr key={user.id}>
                  <td className={tdClassName}>
                    <div className="font-bold text-slate-50">{user.email}</div>
                    <div className="text-xs text-slate-400">ID {user.id}</div>
                  </td>
                  <td className={tdClassName}>
                    <StatusBadge tone={user.is_active ? 'success' : 'danger'}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </StatusBadge>
                  </td>
                  <td className={tdClassName}>
                    <StatusBadge tone={user.mfa_enabled ? 'success' : 'warning'}>
                      {user.mfa_enabled ? 'Enabled' : 'Disabled'}
                    </StatusBadge>
                  </td>
                  <td className={tdClassName}>{user.roles.map((role) => role.name).join(', ') || '—'}</td>
                  <td className={tdClassName}>
                    <select
                      className={inputClassName}
                      defaultValue=""
                      onChange={(event) => {
                        const roleName = event.target.value as RoleName
                        if (roleName) {
                          assignRoleMutation.mutate({ userId: user.id, roleName })
                          event.target.value = ''
                        }
                      }}
                    >
                      <option value="">Select role</option>
                      <option value="admin">admin</option>
                      <option value="user">user</option>
                      <option value="viewer">viewer</option>
                    </select>
                  </td>
                  <td className={tdClassName}>
                    <ConfirmButton
                      className={dangerButtonClassName}
                      confirmMessage={`Delete user ${user.email}? This cannot be undone.`}
                      disabled={deleteUserMutation.isPending}
                      onConfirm={() => deleteUserMutation.mutate(user.id)}
                    >
                      Delete
                    </ConfirmButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableCard>
      )}
    </PageShell>
  )
}
