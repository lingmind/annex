import { activate } from './dsh-plugin.mjs';

export const name = 'lingmind-operator';
export const inject = ['tools', 'skills'];

export async function apply(ctx) {
  await activate(ctx, 'lingmind-operator');
}
