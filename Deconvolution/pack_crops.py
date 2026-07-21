from matplotlib.cbook import contiguous_regions
import numpy as np
import cv2

## Uses the skyline algorithm to pack small images of different sizes into one large atlas 
class Skyline:

    def __init__(self, max_height: int, max_width: int):
        self.max_height = max_height
        self.max_width = max_width

         # stores the skyline by storing the left vertex of the horizontal segments:
        self.skyline:  list[tuple[int, int]] = [(0, 0)]


    def find_position(self, width: int, height: int):
        min_y_idx = -1
        min_y = self.max_height

        for i, (x, y) in enumerate(self.skyline):
            if x + width >= self.max_width:
                continue

            max_x = x + width
            for j in range(i + 1, len(self.skyline)):
                if self.skyline[j][0] > max_x:
                    break
                if self.skyline[j][1] > y:
                    y = self.skyline[j][1]

            if y + height >= self.max_height:
                continue

            if y > min_y:
                continue

            min_y = y
            min_y_idx = i

        if min_y == np.inf or min_y_idx == -1:
            return None

        return (self.skyline[min_y_idx][0], min_y)


    # returns the x and y position of the inserted rectangle
    def insert(self, position: tuple[int, int], width: int, height: int) :
        self.update_skyline(position[0], position[1], width, height)


    def update_skyline(self, x, y, w, h):
        overlapping_vertices = []
        for i, (x_vertex, y_vertex) in enumerate(self.skyline):
            if x <= x_vertex and x_vertex < x + w:
                overlapping_vertices.append(i)

        #  append top left
        self.skyline.append((x, y + h))

        # append bottom right
        last_overlap_height = self.skyline[overlapping_vertices[-1]][1]
        if x + w < self.max_width:
            self.skyline.append((x + w, last_overlap_height))


        for i in reversed(overlapping_vertices):
            self.skyline.pop(i)


        self.skyline.sort(key=lambda x: x[0])



class ImagePacker:

    def __init__(self, atlas_width, atlas_height, padding):

        self._atlas_w = atlas_width
        self._atlas_h = atlas_height
        self.padding = padding

        self.atlas = np.zeros((self._atlas_h, self._atlas_w), dtype=np.uint8)
        self.atlas_density = 0

        self.bbox_map: dict[str, list[tuple[int, int, int, int, int]]] = {} # name -> [(x, y, w, h, idx)]

        self.skyline = Skyline(self._atlas_h, self._atlas_w)


    def finish_current_atlas(self):
        map = self.bbox_map.copy()
        atlas = self.atlas.copy()

        print(f"Atlas density: {self.atlas_density / (self._atlas_h * self._atlas_w)}")
        # reset
        self.bbox_map.clear()
        self.atlas = np.zeros((self._atlas_h, self._atlas_w), dtype=np.uint8)
        self.skyline = Skyline(self._atlas_h, self._atlas_w)

        self.atlas_density = 0

        # atlas = cv2.GaussianBlur(atlas, (5, 5), 0)
        # atlas += 20
        atlas = cv2.bitwise_not(atlas)
        # atlas = cv2.normalize(atlas, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)

        # cv2.imshow("Atlas", atlas)
        # cv2.waitKey(0)

        return atlas, map

    def pack_images(self, image_stack: list[np.ndarray], name: str):
        self.bbox_map[name] = []

        finished_atlases = []
        maps = []

        i = 0
        while i < len(image_stack):
            img = image_stack[i]
            pos = self.skyline.find_position(img.shape[1] + 2 * self.padding, img.shape[0] + 2 * self.padding)

            if pos is None:
                atlas, map = self.finish_current_atlas()

                finished_atlases.append(atlas)
                maps.append(map)

                continue

            self.skyline.insert(pos, img.shape[1] + 2 * self.padding, img.shape[0] + 2 * self.padding)
            x, y = pos

            x += self.padding
            y += self.padding

            self.atlas[y :y + img.shape[0], x:x + img.shape[1]] = img
            self.atlas_density += img.shape[0] * img.shape[1]

            if not name in self.bbox_map:
                self.bbox_map[name] = []
            # self.bbox_map[name].append((x, y, img.shape[1], img.shape[0], i))

            # TODO: remove this test:
            self.bbox_map[name].append((x + 1, y + 1, img.shape[1] - 2, img.shape[0] - 2, i))

            i += 1


        return finished_atlases, maps



if __name__ == "__main__":
    import matplotlib.pyplot as plt
    packer = ImagePacker(1000, 1000, 5)

    N = 100
    widths = np.random.randint(10, 300, size=N)
    heights = np.random.randint(10, 300, size=N)
    values  = np.random.randint(1, 25, size=N)

    image_stack = [np.ones((heights[i], widths[i])) * values[i] for i in range(len(widths))]

    res = packer.pack_images(image_stack, "test")
    plt.imshow(res[0])

    # draw skyline:
    x = [0]
    y = [0]
    for i in range(len(packer.skyline.skyline)):
        x.append(packer.skyline.skyline[i][0])
        y.append(y[-1])
        x.append(packer.skyline.skyline[i][0])
        y.append(packer.skyline.skyline[i][1])
        plt.scatter(packer.skyline.skyline[i][0], packer.skyline.skyline[i][1],
                    marker="x", color="g")

    plt.plot(x, y, "r-")

    plt.show()


    # for img in image_stack:
    #     packer.pack_images([img], "test")
    #
    #     plt.imshow(packer.atlas)
    #
    #     # draw skyline:
    #     x = [0]
    #     y = [0]
    #     for i in range(len(packer.skyline.skyline)):
    #         x.append(packer.skyline.skyline[i][0])
    #         y.append(y[-1])
    #         x.append(packer.skyline.skyline[i][0])
    #         y.append(packer.skyline.skyline[i][1])
    #         plt.scatter(packer.skyline.skyline[i][0], packer.skyline.skyline[i][1],
    #                     marker="x", color="g")
    #
    #     plt.plot(x, y, "r-")
    #
    #     plt.show()

