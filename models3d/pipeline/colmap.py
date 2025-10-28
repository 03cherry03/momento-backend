import os, subprocess, shlex, pathlib

def run(cmd: str, cwd=None):
    print("$", cmd)
    subprocess.run(shlex.split(cmd), cwd=cwd, check=True)

def colmap_from_dir(images_dir: str, work_dir: str) -> str:
    """COLMAP 파이프라인을 간단히 묶어서 실행합니다.
    - feature_extractor
    - exhaustive_matcher (소량 사진 안정적)
    - mapper → sparse
    - image_undistorter → dense
    - patch_match_stereo
    - stereo_fusion → fused.ply
    """
    db = os.path.join(work_dir, "database.db")
    sparse = os.path.join(work_dir, "sparse")
    dense = os.path.join(work_dir, "dense")
    pathlib.Path(sparse).mkdir(parents=True, exist_ok=True)
    pathlib.Path(dense).mkdir(parents=True, exist_ok=True)

    run(f"colmap feature_extractor --database_path {db} --image_path {images_dir} --ImageReader.single_camera 1 --SiftExtraction.peak_threshold 0.006 --SiftExtraction.edge_threshold 10")
    run(f"colmap exhaustive_matcher --database_path {db} --SiftMatching.guided_matching 1")
    run(f"colmap mapper --database_path {db} --image_path {images_dir} --output_path {sparse}")
    run(f"colmap image_undistorter --image_path {images_dir} --input_path {sparse}/0 --output_path {dense} --output_type COLMAP")
    run(f"colmap patch_match_stereo --workspace_path {dense} --workspace_format COLMAP --PatchMatchStereo.geom_consistency true")
    fused_ply = os.path.join(dense, "fused.ply")
    run(f"colmap stereo_fusion --workspace_path {dense} --workspace_format COLMAP --input_type geometric --output_path {fused_ply}")
    return fused_ply
