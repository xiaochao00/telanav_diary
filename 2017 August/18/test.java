public class test {
	public static void main(String[]args) {

		Runtime run = Runtime.getRuntime();
		long max = run.maxMemory();
		long total = run.totalMemory();
		long free = run.freeMemory();
		long usable = max - total + free;
		System.out.println("max memory = " + max);
		System.out.println("already assign = " + total);
		System.out.println("free = " + free);
		System.out.println("max can use = " + usable);
	}
}