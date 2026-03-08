// Exemplo de como modificar seu componente Kanban para usar a API
// Este é um guia - você precisará integrar isso no seu componente existente

import React, { useState, useEffect } from 'react';
import './Kanban.css';
import WebhookStatus from './WebhookStatus';

// Importe as funções da API
import { 
  loadTarefas, 
  createTarefa, 
  updateTarefaStatus, 
  updateTarefaObservacao, 
  deleteTarefa 
} from './kanban-api-example';

const Kanban = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Carrega as tarefas quando o componente é montado
  useEffect(() => {
    carregarTarefas();
  }, []);

  const carregarTarefas = async () => {
    try {
      setLoading(true);
      const tarefasDoBanco = await loadTarefas();
      setTasks(tarefasDoBanco);
      setError(null);
    } catch (err) {
      setError('Erro ao carregar tarefas. Tente novamente.');
      console.error('Erro ao carregar tarefas:', err);
    } finally {
      setLoading(false);
    }
  };

  const [draggedTask, setDraggedTask] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTask, setNewTask] = useState({
    title: '',
    imei: '',
    unidade: '',
    prazo: '',
    observacao: '',
    priority: 'media',
    perfil: '',
    numeroChamado: ''
  });

  const [editingTask, setEditingTask] = useState(null);
  const [editObservacao, setEditObservacao] = useState('');

  const perfis = [
    'Motorista',
    'Promotor',
    'Vendedor',
    'Empregado Geral',
    'KDP',
    'Optimal',
    'ATM',
    'Empregado geral VIP',
    'Empregado geral AD'
  ];

  const columns = [
    { id: 'demanda', title: 'DEMANDA', color: '#9b59b6' },
    { id: 'a-fazer', title: 'A Fazer', color: '#ff6b6b' },
    { id: 'em-andamento', title: 'Em Andamento', color: '#4ecdc4' },
    { id: 'erro', title: 'ERRO', color: '#e74c3c' },
    { id: 'feito', title: 'Feito', color: '#45b7d1' }
  ];

  const handleDragStart = (task) => {
    setDraggedTask(task);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = async (e, columnId) => {
    e.preventDefault();
    if (draggedTask) {
      try {
        // Atualiza no banco de dados
        await updateTarefaStatus(draggedTask.id, columnId);
        
        // Enviar webhook para diferentes colunas
        const eventType = getEventType(columnId);
        if (eventType && draggedTask.status !== columnId) {
          await sendWebhook({ ...draggedTask, status: columnId }, eventType);
        }
        
        // Atualiza o estado local
        const updatedTask = { ...draggedTask, status: columnId };
        setTasks(tasks.map(task => 
          task.id === draggedTask.id 
            ? updatedTask
            : task
        ));
        setDraggedTask(null);
      } catch (error) {
        console.error('Erro ao atualizar status:', error);
        // Opcional: mostrar mensagem de erro para o usuário
        alert('Erro ao atualizar status. Tente novamente.');
      }
    }
  };

  const getEventType = (columnId) => {
    switch (columnId) {
      case 'a-fazer': return 'DEMANDA';
      case 'em-andamento': return 'EM_ANDAMENTO';
      case 'erro': return 'ERRO';
      case 'feito': return 'CONCLUIDO';
      default: return null;
    }
  };

  const addTask = async () => {
    if (newTask.title && newTask.imei && newTask.unidade && newTask.prazo && newTask.perfil) {
      try {
        // Cria a tarefa no banco de dados
        const tarefaCriada = await createTarefa(newTask);
        
        // Adiciona ao estado local
        setTasks([...tasks, tarefaCriada]);
        
        // Limpa o formulário
        setNewTask({
          title: '',
          imei: '',
          unidade: '',
          prazo: '',
          observacao: '',
          perfil: '',
          numeroChamado: '',
          priority: 'media'
        });
        setShowAddForm(false);
      } catch (error) {
        console.error('Erro ao criar tarefa:', error);
        alert('Erro ao criar tarefa. Tente novamente.');
      }
    } else {
      alert('Preencha todos os campos obrigatórios.');
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewTask(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const deleteTask = async (taskId) => {
    if (window.confirm('Tem certeza que deseja deletar esta tarefa?')) {
      try {
        await deleteTarefa(taskId);
        setTasks(tasks.filter(task => task.id !== taskId));
      } catch (error) {
        console.error('Erro ao deletar tarefa:', error);
        alert('Erro ao deletar tarefa. Tente novamente.');
      }
    }
  };

  const startEditObservacao = (task) => {
    setEditingTask(task.id);
    setEditObservacao(task.observacao || '');
  };

  const saveEditObservacao = async () => {
    if (editingTask) {
      try {
        await updateTarefaObservacao(editingTask, editObservacao);
        
        setTasks(tasks.map(task => 
          task.id === editingTask 
            ? { ...task, observacao: editObservacao }
            : task
        ));
        setEditingTask(null);
        setEditObservacao('');
      } catch (error) {
        console.error('Erro ao atualizar observação:', error);
        alert('Erro ao atualizar observação. Tente novamente.');
      }
    }
  };

  const cancelEditObservacao = () => {
    setEditingTask(null);
    setEditObservacao('');
  };

  // Mantenha sua função sendWebhook existente
  const sendWebhook = async (task, eventType = 'EM_ANDAMENTO') => {
    // Sua implementação existente do webhook
    // ...
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'alta': return '#ff4757';
      case 'media': return '#ffa502';
      case 'baixa': return '#2ed573';
      default: return '#747d8c';
    }
  };

  if (loading) {
    return <div className="loading">Carregando tarefas...</div>;
  }

  if (error) {
    return (
      <div className="error">
        <p>{error}</p>
        <button onClick={carregarTarefas}>Tentar novamente</button>
      </div>
    );
  }

  return (
    <div className="kanban-container">
      <div className="kanban-header">
        <h2>Kanban de Processos</h2>
        <button className="add-task-btn" onClick={() => setShowAddForm(true)}>
          + Nova Tarefa
        </button>
        <button className="refresh-btn" onClick={carregarTarefas} title="Atualizar tarefas">
          🔄 Atualizar
        </button>
      </div>

      {/* Seu formulário de adição de tarefa existente */}
      {showAddForm && (
        <div className="add-task-modal">
          <div className="modal-content">
            <h3>Nova Tarefa</h3>
            {/* Seu formulário existente - sem mudanças */}
            <div className="form-group">
              <label>Título:</label>
              <input
                type="text"
                name="title"
                value={newTask.title}
                onChange={handleInputChange}
                placeholder="Digite o título da tarefa"
              />
            </div>
            {/* Resto do seu formulário... */}
            <div className="form-actions">
              <button className="cancel-btn" onClick={() => setShowAddForm(false)}>
                Cancelar
              </button>
              <button className="save-btn" onClick={addTask}>
                Salvar Tarefa
              </button>
            </div>
          </div>
        </div>
      )}
      
      <div className="kanban-board">
        {columns.map(column => (
          <div
            key={column.id}
            className="kanban-column"
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, column.id)}
          >
            <div className="column-header" style={{ backgroundColor: column.color }}>
              <h3>{column.title}</h3>
              <span className="task-count">
                {tasks.filter(task => task.status === column.id).length}
              </span>
            </div>
            
            <div className="column-content">
              {tasks
                .filter(task => task.status === column.id)
                .map(task => (
                  <div
                    key={task.id}
                    className="task-card"
                    draggable
                    onDragStart={() => handleDragStart(task)}
                  >
                    <div className="task-header">
                      <span 
                        className="priority-badge"
                        style={{ backgroundColor: getPriorityColor(task.priority) }}
                      >
                        {task.priority.toUpperCase()}
                      </span>
                      <div className="task-actions">
                        {task.status === 'em-andamento' && (
                          <button 
                            className="edit-btn"
                            onClick={() => startEditObservacao(task)}
                            title="Editar observação"
                          >
                            ✏️
                          </button>
                        )}
                        <button 
                          className="delete-btn"
                          onClick={() => deleteTask(task.id)}
                        >
                          ×
                        </button>
                      </div>
                    </div>
                    <div className="task-content">
                      <p><strong>{task.title}</strong></p>
                      <div className="task-details">
                        <span className="detail-item">📱 {task.imei}</span>
                        <span className="detail-item">🏢 {task.unidade}</span>
                        <span className="detail-item">📞 {task.numero_chamado}</span>
                        <span className="detail-item">👤 {task.perfil}</span>
                        <span className="detail-item">📅 {task.prazo}</span>
                      </div>
                      {task.observacao && (
                        <div className="task-observacao">
                          {editingTask === task.id ? (
                            <div className="edit-observacao">
                              <textarea
                                value={editObservacao}
                                onChange={(e) => setEditObservacao(e.target.value)}
                                placeholder="Adicione observações..."
                                rows="3"
                                autoFocus
                              />
                              <div className="edit-actions">
                                <button className="save-edit-btn" onClick={saveEditObservacao}>
                                  Salvar
                                </button>
                                <button className="cancel-edit-btn" onClick={cancelEditObservacao}>
                                  Cancelar
                                </button>
                              </div>
                            </div>
                          ) : (
                            <small>📝 {task.observacao}</small>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        ))}
      </div>
      
      <WebhookStatus />
    </div>
  );
};

export default Kanban;
