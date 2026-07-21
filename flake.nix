{
inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    flake-utils = {
        url = "github:numtide/flake-utils";
        inputs.system.follows = "systems";
    };
};

outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem
    (system:
    let
        pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
			config.cudaSupport = true;
        };
        libs = [
            pkgs.libcxx
			pkgs.hdf5
			# pkgs.libtorch-bin
			# pkgs.cudaPackages.cuda_nvrtc
        ];
    in
        with pkgs;
            {
            devShells.default = mkShell {
                nativeBuildInputs = with pkgs; [
                    bashInteractive
                    (opencv.override ({
                        enableGtk3 = true;
                        enableCuda = false;
                        enableFfmpeg = true;
                        enableUnfree = true;
                    }))
                    cmake
                    libgcc
                    libcxx
                    pkg-config
                    gcc
                    hdf5
					mpi
                    (pkgs.python312.withPackages(ps: with ps;[
						# (torch.override ({cudaSupport = true;}))
						# torchvision
						torch-bin
						torchvision-bin
						(opencv4.override {enableGtk3 = true; enableCuda = false;})
						h5py
						matplotlib
					]))
                ];
                buildInputs = with pkgs; [
                ];
                shellHook = ''
                '';
                LD_LIBRARY_PATH = "${pkgs.lib.makeLibraryPath libs}";
            };
        }
    );
}
