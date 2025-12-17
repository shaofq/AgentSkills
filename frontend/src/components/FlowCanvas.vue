<script setup lang="ts">
import { ref, watch } from 'vue'
import { VueFlow, useVueFlow, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { useWorkflowStore } from '@/stores/workflow'
import AgentNode from './nodes/AgentNode.vue'
import InputNode from './nodes/InputNode.vue'
import OutputNode from './nodes/OutputNode.vue'
import ConditionNode from './nodes/ConditionNode.vue'
import ParallelNode from './nodes/ParallelNode.vue'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

const emit = defineEmits<{
  (e: 'node-click'): void
}>()

const store = useWorkflowStore()
const { onConnect, addEdges, onNodesChange, onEdgesChange, applyNodeChanges, applyEdgeChanges } = useVueFlow()

const nodeTypes = {
  agent: AgentNode,
  input: InputNode,
  output: OutputNode,
  condition: ConditionNode,
  parallel: ParallelNode,
}

let nodeId = 0
function getId() {
  return `node_${nodeId++}`
}

function onDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

function onDrop(event: DragEvent) {
  event.preventDefault()
  
  const data = event.dataTransfer?.getData('application/json')
  if (!data) return
  
  const item = JSON.parse(data)
  const bounds = (event.target as HTMLElement).getBoundingClientRect()
  
  const position = {
    x: event.clientX - bounds.left - 75,
    y: event.clientY - bounds.top - 25,
  }
  
  const newNode = {
    id: getId(),
    type: item.type,
    position,
    data: {
      label: item.label,
      icon: item.icon,
      color: item.color,
      agentConfig: item.agentConfig,
    },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  }
  
  store.addNode(newNode as any)
}

function onNodeClick(event: any) {
  const node = event.node || event
  if (node && node.id) {
    store.selectNode(node.id)
    emit('node-click')
  }
}

function onPaneClick() {
  store.selectNode(null)
}

onConnect((params) => {
  const edge = {
    id: `edge_${params.source}_${params.target}`,
    source: params.source,
    target: params.target,
    sourceHandle: params.sourceHandle,
    targetHandle: params.targetHandle,
    animated: true,
    style: { stroke: '#6366f1', strokeWidth: 2 },
  }
  store.addEdge(edge as any)
})

onNodesChange((changes) => {
  applyNodeChanges(changes)
})

onEdgesChange((changes) => {
  applyEdgeChanges(changes)
})

watch(() => store.nodes, (newNodes) => {
  // 同步节点变化
}, { deep: true })
</script>

<template>
  <div class="w-full h-full">
    <VueFlow
      v-model:nodes="store.nodes"
      v-model:edges="store.edges"
      :node-types="nodeTypes"
      :default-viewport="{ zoom: 1.2, x: 0, y: 0 }"
      :min-zoom="0.2"
      :max-zoom="4"
      @dragover="onDragOver"
      @drop="onDrop"
      @node-click="onNodeClick"
      @pane-click="onPaneClick"
      class="bg-gray-50"
    >
      <Background pattern-color="#e5e7eb" :gap="20" />
      <Controls position="bottom-right" />
      <MiniMap 
        position="bottom-left" 
        :pannable="true" 
        :zoomable="true"
        class="!bg-white !border !border-gray-200 !rounded-lg !shadow-sm"
      />
      
      <!-- 空状态提示 -->
      <template #empty>
        <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div class="text-center text-gray-400">
            <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
            </svg>
            <p class="text-lg font-medium">从左侧拖拽组件开始编排</p>
            <p class="text-sm mt-1">连接节点以创建工作流</p>
          </div>
        </div>
      </template>
    </VueFlow>
  </div>
</template>

<style>
.vue-flow__node {
  border-radius: 8px;
}

.vue-flow__handle {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #6366f1;
  border: 2px solid white;
}

.vue-flow__handle:hover {
  background: #4f46e5;
}

.vue-flow__edge-path {
  stroke: #6366f1;
  stroke-width: 2;
}

.vue-flow__edge.selected .vue-flow__edge-path {
  stroke: #4f46e5;
  stroke-width: 3;
}
</style>
