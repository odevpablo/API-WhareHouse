// Exemplo de como integrar o componente Kanban com a API
// Substitua as funções do seu componente React com estas

const API_BASE_URL = 'http://localhost:8000/api'; // Ajuste para sua URL

// Função para carregar todas as tarefas
export const loadTarefas = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/tarefas`);
    if (!response.ok) throw new Error('Erro ao carregar tarefas');
    return await response.json();
  } catch (error) {
    console.error('Erro ao carregar tarefas:', error);
    return [];
  }
};

// Função para criar uma nova tarefa
export const createTarefa = async (tarefaData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/tarefas`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(tarefaData),
    });
    
    if (!response.ok) throw new Error('Erro ao criar tarefa');
    return await response.json();
  } catch (error) {
    console.error('Erro ao criar tarefa:', error);
    throw error;
  }
};

// Função para atualizar o status de uma tarefa (drag and drop)
export const updateTarefaStatus = async (tarefaId, status, observacao = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/tarefas/${tarefaId}/status`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        status: status,
        observacao: observacao
      }),
    });
    
    if (!response.ok) throw new Error('Erro ao atualizar status');
    return await response.json();
  } catch (error) {
    console.error('Erro ao atualizar status:', error);
    throw error;
  }
};

// Função para atualizar apenas a observação
export const updateTarefaObservacao = async (tarefaId, observacao) => {
  try {
    const response = await fetch(`${API_BASE_URL}/tarefas/${tarefaId}/observacao`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        observacao: observacao
      }),
    });
    
    if (!response.ok) throw new Error('Erro ao atualizar observação');
    return await response.json();
  } catch (error) {
    console.error('Erro ao atualizar observação:', error);
    throw error;
  }
};

// Função para deletar uma tarefa
export const deleteTarefa = async (tarefaId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/tarefas/${tarefaId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) throw new Error('Erro ao deletar tarefa');
    return await response.json();
  } catch (error) {
    console.error('Erro ao deletar tarefa:', error);
    throw error;
  }
};

// Função para obter resumo do Kanban
export const getKanbanSummary = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/kanban/summary`);
    if (!response.ok) throw new Error('Erro ao obter resumo');
    return await response.json();
  } catch (error) {
    console.error('Erro ao obter resumo:', error);
    return null;
  }
};
