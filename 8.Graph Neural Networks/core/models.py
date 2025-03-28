# -*- coding:utf-8 -*-
import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import GATConv, GCNConv, SAGEConv, SGConv


class GCN(torch.nn.Module):
    def __init__(self, in_feats, h_feats, out_feats):
        super(GCN, self).__init__()
        self.conv1 = GCNConv(in_feats, h_feats)
        self.conv2 = GCNConv(h_feats, out_feats)

    def forward(self, data, return_hidden=False):
        x, edge_index = data.x, data.edge_index
        x = F.dropout(x, p=0.6, training=self.training)
        x_hidden = F.relu(self.conv1(x, edge_index))
        x = self.conv2(x_hidden, edge_index)

        if return_hidden:
            return x_hidden  # [num_nodes, hidden_dim]
        else:
            return x  # [num_nodes, num_classes]


class GraphSAGE(torch.nn.Module):
    def __init__(self, in_feats, h_feats, out_feats):
        super(GraphSAGE, self).__init__()
        self.conv1 = SAGEConv(in_feats, h_feats, normalize=True)
        self.conv2 = SAGEConv(h_feats, out_feats, normalize=True)

    def forward(self, data, return_hidden=False):
        x, edge_index = data.x, data.edge_index
        x = F.dropout(x, p=0.6, training=self.training)
        x_hidden = F.relu(self.conv1(x, edge_index))
        x = self.conv2(x_hidden, edge_index)
        if return_hidden:
            return x_hidden  # [num_nodes, hidden_dim]
        else:
            return x  # [num_nodes, num_classes]
        return x


class GAT(torch.nn.Module):
    def __init__(self, in_feats, h_feats, out_feats):
        super(GAT, self).__init__()
        self.conv1 = GATConv(in_feats, h_feats, heads=8, concat=False)
        self.conv2 = GATConv(h_feats, out_feats, heads=8, concat=False)

    def forward(self, data, return_hidden=False):
        x, edge_index = data.x, data.edge_index
        x = F.dropout(x, p=0.6, training=self.training)
        x_hidden = F.relu(self.conv1(x, edge_index))
        x = self.conv2(x_hidden, edge_index)
        if return_hidden:
            return x_hidden  # [num_nodes, hidden_dim]
        else:
            return x  # [num_nodes, num_classes]
        return x
