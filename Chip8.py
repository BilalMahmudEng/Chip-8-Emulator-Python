# Author: Bilal Mahmud

import tkinter as tk
import time
import sys
import random
import keyboard
import time
import winsound


class Chip8:
    def __init__(self):
        self.FONT = None
        self.mem = [0x00] * 4096
        self.V = [0] * 16
        self.stack = []
        self.I = 0
        self.PC = 0x200
        self.delay_timer = 0
        self.sound_timer = 0
        self.font()
        self.opcode = 0
        self.pixel_state = [[False for x in range(64)] for x in range(32)]
        self.root = tk.Tk()
        self.scale = 25
        self.canvas = tk.Canvas(self.root, width=64 * self.scale, height=32 * self.scale)
        self.canvas.pack()
        self.keymap = {0x0: '1', 0x1: '2', 0x2: '3', 0x3: '4',
                       0x4: 'q', 0x5: 'w', 0x6: 'e', 0x7: 'r',
                       0x8: 'a', 0x9: 's', 0xA: 'd', 0xB: 'f',
                       0xC: 'z', 0xD: 'x', 0xE: 'c', 0xF: 'v'}

    def draw(self):
        self.canvas.delete("all")
        for i in range(32):
            for j in range(64):
                if self.pixel_state[i][j]:
                    iscale = i * self.scale
                    jscale = j * self.scale
                    self.canvas.create_rectangle(jscale, i * self.scale, (jscale + self.scale),
                                                 (iscale + self.scale), fill="black", outline="")
        self.canvas.update()

    def font(self):
        self.FONT = [0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
                     0x20, 0x60, 0x20, 0x20, 0x70,  # 1
                     0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
                     0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
                     0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
                     0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
                     0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
                     0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
                     0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
                     0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
                     0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
                     0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
                     0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
                     0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
                     0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
                     0xF0, 0x80, 0xF0, 0x80, 0x80]  # F
        for i in range(len(self.FONT)):
            self.mem[i] = self.FONT[i]

    def fetch_decode(self):
        read1 = self.mem[self.PC]
        read2 = self.mem[self.PC + 1]
        self.opcode = read1 << 8 | read2

        first = self.opcode & 0xF000
        second = (self.opcode & 0x0F00) >> 8
        third = (self.opcode & 0x00F0) >> 4
        fourth = self.opcode & 0x000F

        match self.opcode:
            # clear screen
            case 0x00E0:
                self.pixel_state = [[False for i in range(64)] for i in range(32)]
                self.PC += 2
            # return from subroutine
            case 0x00EE:
                self.PC = self.stack.pop()

        match first:
            # Jumps to The particular address
            case 0x1000:
                self.PC = (self.opcode & 0x0FFF)
            # Pushes the specified address to the stack (subroutine)
            case 0x2000:
                self.stack.append((self.PC + 2))
                self.PC = (self.opcode & 0x0FFF)

            # Skips next instruction if Vx is equal to specified address
            case 0x3000:
                if (self.V[second]) == (self.opcode & 0x00FF):
                    self.PC += 4
                else:
                    self.PC += 2
            # Skips next instruction if Vx is not equal to specified address
            case 0x4000:
                if (self.V[second]) != (self.opcode & 0x00FF):
                    self.PC += 4
                else:
                    self.PC += 2
            # Skips next instruction if Vx= Vy
            case 0x5000:
                if (self.V[second]) == (self.V[third]):
                    self.PC += 4
                else:
                    self.PC += 2
            # Sets Vx to specified address
            case 0x6000:
                self.V[second] = (self.opcode & 0x00FF)
                self.PC += 2
            # Sets Vx = Vx + Vy with no carry
            case 0x7000:
                self.V[second] = (self.V[second] + (self.opcode & 0x00FF)) & 0xFF
                self.PC += 2

            case 0x8000:
                match fourth:
                    # Sets Vx = Vy
                    case 0x0000:
                        self.V[second] = self.V[third]
                        self.PC += 2
                    # Sets Vx = Vx OR Vy
                    case 0x0001:
                        self.V[second] = self.V[second] | self.V[third]
                        self.PC += 2
                    # Sets Vx = Vx AND Vy
                    case 0x0002:
                        self.V[second] = self.V[second] & self.V[third]
                        self.PC += 2
                    # Sets Vx = Vx XOR Vy
                    case 0x0003:
                        self.V[second] = self.V[second] ^ self.V[third]
                        self.PC += 2
                    # Sets Vx = Vx + Vy and stores the carry in VF
                    case 0x0004:
                        sum = self.V[second] + self.V[third]
                        if sum > 0xFF:
                            self.V[0xF] = 1
                        else:
                            self.V[0xF] = 0
                        self.V[second] = sum & 0xFF
                        self.PC += 2
                    # Sets Vx = Vx - Vy and stores the borrow in VF
                    case 0x0005:
                        if self.V[second] > self.V[third]:
                            self.V[0xF] = 1
                        else:
                            self.V[0xF] = 0
                        self.V[second] = (self.V[second] - self.V[third]) & 0xFF
                        self.PC += 2
                    # Shifts Vx right by 1 and stores the LSB in VF
                    case 0x0006:
                        self.V[0xF] = self.V[second] & 0x0001
                        self.V[second] = self.V[second] >> 1
                        self.PC += 2
                    # Sets Vx = Vy - Vx and stores the borrow in VF
                    case 0x0007:
                        if self.V[third] > self.V[second]:
                            self.V[0xF] = 0
                        else:
                            self.V[0xF] = 1
                        self.V[second] = (self.V[third] - self.V[second]) & 0xFF
                        self.PC += 2
                    # Shifts Vx left by 1 and stores the MSB in VF
                    case 0x000E:
                        self.V[0xF] = (self.V[second] >> 7) & 0x0001
                        self.V[second] = self.V[second] << 1 & 0xFF
                        self.PC += 2
            # Skips next instruction if Vx != Vy
            case 0x9000:
                if (self.V[second]) != (self.V[third]):
                    self.PC += 4
                else:
                    self.PC += 2
            # Sets I equal to the specified address
            case 0xA000:
                self.I = self.opcode & 0x0FFF
                self.PC += 2
            # Jumps to the specified address plus V0
            case 0xB000:
                self.PC = self.V[0x0] + (self.opcode & 0x0FFF)
            # Sets Vx = specified address & random number between 0 and 255
            case 0xC000:
                rand = random.randint(0, 255)
                self.V[second] = rand & (self.opcode & 0x00FF)
                self.PC += 2

            case 0xD000:
                x = self.V[second] % 64
                y = self.V[third] % 32
                height = fourth
                self.V[0xF] = 0

                for row in range(height):
                    sprite_byte = self.mem[self.I + row]
                    for col in range(8):
                        sprite_pixel = (sprite_byte >> (7 - col)) & 1
                        if sprite_pixel == 1:
                            x_pos = (x + col) % 64
                            y_pos = (y + row) % 32
                            if self.pixel_state[y_pos][x_pos] == 1:
                                self.V[0xF] = 1
                            self.pixel_state[y_pos][x_pos] = self.pixel_state[y_pos][x_pos] ^ 1
                self.PC += 2

            case 0xE000:
                match (self.opcode & 0x00FF):
                    # Skips instruction when Vx key is pressed
                    case 0x009E:
                        try:
                            if self.V[second] in self.keymap and keyboard.is_pressed(self.keymap[self.V[second]]):
                                self.PC += 4
                            else:
                                self.PC += 2
                        except:
                            self.PC += 2
                    # Skips instruction when Vx key not pressed
                    case 0x00A1:
                        try:
                            if self.V[second] in self.keymap and keyboard.is_pressed(self.keymap[self.V[second]]):
                                self.PC += 2
                            else:
                                self.PC += 4
                        except:
                            self.PC += 2
            case 0xF000:
                match (self.opcode & 0x00FF):
                    # Sets Vx = Delay Timer
                    case 0x0007:
                        self.V[second] = self.delay_timer
                        self.PC += 2
                    # Sets Vx equal to the key pressed, stops program until this happens
                    case 0x000A:
                        for code1, code in self.keymap.items():
                            if keyboard.is_pressed(code):
                                self.V[second] = code1
                                self.PC += 2
                                return
                    case 0x0015:
                        self.delay_timer = self.V[second]
                        self.PC += 2
                    case 0x0018:
                        self.sound_timer = self.V[second]
                        self.PC += 2
                    case 0x001E:
                        self.I += self.V[second]
                        self.PC += 2
                    case 0x0029:
                        self.I = self.V[second] * 5
                        self.PC += 2
                    case 0x0033:
                        self.mem[self.I] = self.V[second] // 100
                        self.mem[self.I + 1] = (self.V[second] // 10) % 10
                        self.mem[self.I + 2] = self.V[second] % 10
                        self.PC += 2
                    case 0x0055:
                        count = 0
                        while count < second + 1:
                            self.mem[self.I + count] = self.V[count]
                            count += 1
                        self.PC += 2
                    case 0x0065:
                        count = 0
                        while count < second + 1:
                            self.V[count] = self.mem[self.I + count]
                            count += 1
                        self.PC += 2
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
            winsound.Beep(400, 50)

    def run(self):
        self.font()
        a = time.time()
        while True:
            time.sleep(1 / 600)
            self.fetch_decode()
            self.fetch_decode()
            self.fetch_decode()
            self.draw()
            if time.time() - a >= 1 / 60:
                a = time.time()
            self.root.update()

    def rom(self, filename):
        with open(filename, 'rb') as f:
            game = f.read()
        count = 0
        while count != len(game):
            self.mem[0x200 + count] = game[count]
            count += 1


if __name__ == "__main__":
    load = Chip8()
    load.rom('pong.rom')
    load.run()
