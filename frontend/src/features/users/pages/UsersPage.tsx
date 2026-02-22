import { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { UsersTable } from '../components/UsersTable';
import { UserModal } from '../components/UserModal';
import { userService } from '../services/userService';
import { User, CreateUserRequest, UpdateUserRequest } from '../types';
import '../styles.css';

export const UsersPage = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const data = await userService.getAll();
      setUsers(data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleAdd = () => {
    setSelectedUser(null);
    setIsModalOpen(true);
  };

  const handleEdit = (user: User) => {
    setSelectedUser(user);
    setIsModalOpen(true);
  };

  const handleSave = async (data: CreateUserRequest | UpdateUserRequest) => {
    if (selectedUser) {
      await userService.update(selectedUser.id, data as UpdateUserRequest);
    } else {
      await userService.create(data as CreateUserRequest);
    }
    fetchUsers(); // Refresh list
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Вы уверены, что хотите удалить этого пользователя?')) {
      try {
        await userService.delete(id);
        fetchUsers();
      } catch (error) {
        console.error('Failed to delete user:', error);
      }
    }
  };

  return (
    <div className="container">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold mb-1">Пользователи</h1>
          <p className="text-muted">Управление доступом и сотрудниками</p>
        </div>
        
        <button 
          onClick={handleAdd}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={20} />
          <span>Добавить</span>
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          {/* Simple loader styling if not available globally */}
          <div className="loader" style={{ 
            width: '32px', 
            height: '32px', 
            border: '3px solid rgba(255,255,255,0.1)', 
            borderLeftColor: 'var(--color-primary)', 
            borderRadius: '50%', 
            animation: 'spin 1s linear infinite' 
          }} />
        </div>
      ) : (
        <UsersTable 
          users={users} 
          onEdit={handleEdit} 
          onDelete={handleDelete} 
        />
      )}

      <UserModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleSave}
        user={selectedUser}
      />
    </div>
  );
};
