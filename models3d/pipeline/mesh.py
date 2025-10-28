import open3d as o3d
import trimesh

def poisson_to_glb(fused_ply: str, out_mesh_path: str, out_glb_path: str, depth: int = 10):
    """fused.ply를 메쉬로 재구성하고, 아티팩트 정리 후 GLB로 내보냅니다.
    depth=9~11 정도가 속도/품질 균형 측면에서 무난합니다.
    """
    pcd = o3d.io.read_point_cloud(fused_ply)
    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.05, max_nn=30))

    mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=depth)
    mesh.compute_vertex_normals()

    mesh = mesh.remove_degenerate_triangles()
    mesh = mesh.remove_duplicated_triangles()
    mesh = mesh.remove_duplicated_vertices()
    mesh = mesh.remove_non_manifold_edges()

    target = int(len(mesh.triangles) * 0.5)
    if target > 0:
        mesh = mesh.simplify_quadric_decimation(target)

    o3d.io.write_triangle_mesh(out_mesh_path, mesh)

    tmesh = trimesh.load(out_mesh_path, force='mesh')
    tmesh.export(out_glb_path)
