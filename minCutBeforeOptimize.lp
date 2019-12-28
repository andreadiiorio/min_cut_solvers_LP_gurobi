\ Model minCut
\ LP format - for model browsing. Use MPS format to capture full model detail.
Minimize
  edge[0,1,1] + edge[0,2,1] + edge[1,0,1] + edge[1,2,1] + edge[2,0,1]
   + edge[2,1,1] + 999999 edge[2,-1,999999] + 999999 edge[-2,0,999999]
Subject To
 R0: - z_node[0] + z_node[1] + edge[0,1,1] >= 0
 R1: - z_node[0] + z_node[2] + edge[0,2,1] >= 0
 R2: z_node[0] - z_node[1] + edge[1,0,1] >= 0
 R3: - z_node[1] + z_node[2] + edge[1,2,1] >= 0
 R4: z_node[0] - z_node[2] + edge[2,0,1] >= 0
 R5: z_node[1] - z_node[2] + edge[2,1,1] >= 0
 R6: - z_node[2] + edge[2,-1,999999] >= 0
 R7: z_node[0] + edge[-2,0,999999] >= 1
 sign_edge[0,1,1]: edge[0,1,1] >= 0
 sign_edge[0,2,1]: edge[0,2,1] >= 0
 sign_edge[1,0,1]: edge[1,0,1] >= 0
 sign_edge[1,2,1]: edge[1,2,1] >= 0
 sign_edge[2,0,1]: edge[2,0,1] >= 0
 sign_edge[2,1,1]: edge[2,1,1] >= 0
 sign_edge[2,-1,999999]: edge[2,-1,999999] >= 0
 sign_edge[-2,0,999999]: edge[-2,0,999999] >= 0
 sign_edge[0]: z_node[0] >= -1e+100
 sign_edge[1]: z_node[1] >= -1e+100
 sign_edge[2]: z_node[2] >= -1e+100
Bounds
End
