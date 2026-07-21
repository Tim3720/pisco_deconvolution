from Deconvolution.parser import parse_config_file
from Deconvolution.writer import write_crops
from Deconvolution.pack_crops import ImagePacker
from Deconvolution.deconvolution_model import DeconvolutionModel
from Deconvolution.reader import Reader
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=str)

    args = parser.parse_args()
    config_path = args.config

    settings = parse_config_file(config_path)

    reader = Reader(settings.datapath)

    packer = ImagePacker(2600, 2600, 5)

    model = DeconvolutionModel()
    model.load_model()

    batch = []
    deconvolved = []
    maps = []
    total_images = 0
    total_batch_size = 0
    total_groups = 0
    while not reader.is_last_file():
        filename = reader.open_next_file()
        print("Starting file", filename)

        while not reader.is_last_group():
            name, images = reader.get_next_group_images()
            total_images += len(images)
            total_groups += 1

            res, _maps = packer.pack_images(images, name)

            batch.extend(res)
            maps.extend(_maps)

            if len(batch) >= 4:
                print("Running batch...")
                model.run_deconvolution(batch, deconvolved)

                write_crops(deconvolved, maps, filename)

                total_batch_size += len(batch)
                batch = []
                deconvolved.clear()
                maps.clear()


        # End of file, finish current atlas and process batch if not empty:

        atlas, map = packer.finish_current_atlas()
        batch.append(atlas)
        maps.append(map)

        if len(batch) > 0:
            print("Running batch...")
            model.run_deconvolution(batch, deconvolved)

            total_batch_size += len(batch)
            batch = []

            write_crops(deconvolved, maps, filename)
            deconvolved.clear()
            maps.clear()

        reader.close_current_file()
        print("Finished file", filename)

    print("Total images:", total_images)
    print("Total groups:", total_groups)
    print("Total batch size:", total_batch_size)


if __name__ == "__main__":
    main()
